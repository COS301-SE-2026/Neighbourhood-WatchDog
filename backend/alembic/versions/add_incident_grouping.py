"""add incident grouping

Revision ID: add_incident_grouping
Revises: 05696974518c, 7eadb5195151, a7f3c9d1e2b4
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_incident_grouping"

down_revision: Union[str, Sequence[str], None] = "merge_pre_incident_heads"

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "detection_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_incident_detection_last_seen",
        "incident",
        ["detection_type", "last_seen_at"],
        unique=False,
    )

    op.add_column(
        "alert",
        sa.Column(
            "incident_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_alert_incident_id",
        "alert",
        ["incident_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_alert_incident_id",
        "alert",
        "incident",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill existing alerts.
    #
    # Weapon alerts on the same camera are grouped when they are OPEN
    # and occur within 30 seconds. Other alerts get their own Incident.
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                current_incident UUID := NULL;
                current_camera UUID := NULL;
                current_detection_type TEXT := NULL;
                current_last_seen TIMESTAMPTZ := NULL;
                current_is_open BOOLEAN := FALSE;
                alert_row RECORD;
            BEGIN
                FOR alert_row IN
                    SELECT
                        id,
                        camera_id,
                        detection_type::text AS detection_type,
                        status,
                        frame_timestamp,
                        created_at
                    FROM alert
                    WHERE incident_id IS NULL
                    ORDER BY
                        camera_id,
                        detection_type,
                        frame_timestamp,
                        created_at,
                        id
                LOOP
                    IF
                        alert_row.detection_type = 'WEAPON_DETECTED'
                        AND alert_row.status = 'OPEN'
                        AND current_incident IS NOT NULL
                        AND current_camera = alert_row.camera_id
                        AND current_detection_type = alert_row.detection_type
                        AND current_is_open = TRUE
                        AND alert_row.frame_timestamp
                            <= current_last_seen + INTERVAL '30 seconds'
                    THEN
                        current_last_seen = alert_row.frame_timestamp;

                        UPDATE incident
                        SET last_seen_at = alert_row.frame_timestamp
                        WHERE id = current_incident;
                    ELSE
                        current_incident = gen_random_uuid();
                        current_camera = alert_row.camera_id;
                        current_detection_type = alert_row.detection_type;
                        current_last_seen = alert_row.frame_timestamp;
                        current_is_open = alert_row.status = 'OPEN';

                        INSERT INTO incident (
                            id,
                            detection_type,
                            started_at,
                            last_seen_at,
                            created_at
                        )
                        VALUES (
                            current_incident,
                            alert_row.detection_type,
                            alert_row.frame_timestamp,
                            alert_row.frame_timestamp,
                            alert_row.created_at
                        );
                    END IF;

                    UPDATE alert
                    SET incident_id = current_incident
                    WHERE id = alert_row.id;
                END LOOP;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_alert_incident_id",
        "alert",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_alert_incident_id",
        table_name="alert",
    )

    op.drop_column(
        "alert",
        "incident_id",
    )

    op.drop_index(
        "ix_incident_detection_last_seen",
        table_name="incident",
    )

    op.drop_table("incident")