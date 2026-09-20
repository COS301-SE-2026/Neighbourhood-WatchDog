"""add tracking subject and sighting tables

Revision ID: 7eadb5195151
Revises: 548f8f4f39f0
Create Date: 2026-09-15 21:28:04.228689

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7eadb5195151'
down_revision = '548f8f4f39f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tracking_subject",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alert.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alert_id",
            name="uq_tracking_subject_alert",
        ),
    )

    op.create_table(
        "tracking_sighting",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tracking_subject_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "local_track_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "observed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "sequence_no",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "match_confidence",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sequence_no > 0",
            name="ck_tracking_sighting_sequence_positive",
        ),
        sa.CheckConstraint(
            "match_confidence IS NULL OR "
            "(match_confidence >= 0 AND match_confidence <= 1)",
            name="ck_tracking_sighting_confidence_range",
        ),
        sa.ForeignKeyConstraint(
            ["tracking_subject_id"],
            ["tracking_subject.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["camera.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tracking_subject_id",
            "sequence_no",
            name="uq_tracking_sighting_subject_sequence",
        ),
    )

    op.create_index(
        "ix_tracking_sighting_subject_observed_at",
        "tracking_sighting",
        ["tracking_subject_id", "observed_at"],
        unique=False,
    )

    op.create_index(
        "ix_tracking_sighting_camera_observed_at",
        "tracking_sighting",
        ["camera_id", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tracking_sighting_camera_observed_at",
        table_name="tracking_sighting",
    )

    op.drop_index(
        "ix_tracking_sighting_subject_observed_at",
        table_name="tracking_sighting",
    )

    op.drop_table("tracking_sighting")
    op.drop_table("tracking_subject")