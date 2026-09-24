"""unify alert lifecycle

Revision ID: 0b498cd245b5
Revises: a0e51455c92c
Create Date: 2026-09-22 12:40:33.208745
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0b498cd245b5"
down_revision: Union[str, Sequence[str], None] = "a0e51455c92c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the unified alert lifecycle fields."""

    op.add_column(
        "alert",
        sa.Column(
            "acknowledged_by",
            sa.UUID(),
            nullable=True,
        ),
    )
    op.add_column(
        "alert",
        sa.Column(
            "acknowledged_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "alert",
        sa.Column(
            "confirmed_by",
            sa.UUID(),
            nullable=True,
        ),
    )
    op.add_column(
        "alert",
        sa.Column(
            "confirmed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "alert_acknowledged_by_fkey",
        "alert",
        "users",
        ["acknowledged_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "alert_confirmed_by_fkey",
        "alert",
        "users",
        ["confirmed_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Existing ACKNOWLEDGED alerts incorrectly used the
    # resolved fields. Move that information into the new fields.
    op.execute(
        """
        UPDATE alert
        SET
            acknowledged_by = resolved_by,
            acknowledged_at = resolved_at,
            resolved_by = NULL,
            resolved_at = NULL
        WHERE status = 'ACKNOWLEDGED'
        """
    )

    # Existing RESOLVED alerts are treated as previously
    # acknowledged and confirmed incidents.
    op.execute(
        """
        UPDATE alert
        SET
            acknowledged_by = COALESCE(
                acknowledged_by,
                resolved_by
            ),
            acknowledged_at = COALESCE(
                acknowledged_at,
                resolved_at
            ),
            confirmed_by = COALESCE(
                confirmed_by,
                resolved_by
            ),
            confirmed_at = COALESCE(
                confirmed_at,
                resolved_at
            )
        WHERE status = 'RESOLVED'
        """
    )

    op.create_check_constraint(
        "ck_alert_status",
        "alert",
        """
        status IN (
            'OPEN',
            'ACKNOWLEDGED',
            'CONFIRMED',
            'RESOLVED',
            'DISMISSED'
        )
        """,
    )

    op.create_check_constraint(
        "ck_alert_acknowledged_fields_pair",
        "alert",
        """
        (
            acknowledged_by IS NULL
            AND acknowledged_at IS NULL
        )
        OR
        (
            acknowledged_by IS NOT NULL
            AND acknowledged_at IS NOT NULL
        )
        """,
    )

    op.create_check_constraint(
        "ck_alert_confirmed_fields_pair",
        "alert",
        """
        (
            confirmed_by IS NULL
            AND confirmed_at IS NULL
        )
        OR
        (
            confirmed_by IS NOT NULL
            AND confirmed_at IS NOT NULL
        )
        """,
    )


def downgrade() -> None:
    """Restore the previous alert lifecycle structure."""

    # The old application only understands OPEN,
    # ACKNOWLEDGED and RESOLVED.
    op.execute(
        """
        UPDATE alert
        SET status = 'ACKNOWLEDGED'
        WHERE status IN ('CONFIRMED', 'DISMISSED')
        """
    )

    # Restore the old behaviour where acknowledgement information
    # was stored in the resolved fields.
    op.execute(
        """
        UPDATE alert
        SET
            resolved_by = COALESCE(
                resolved_by,
                acknowledged_by,
                confirmed_by
            ),
            resolved_at = COALESCE(
                resolved_at,
                acknowledged_at,
                confirmed_at
            )
        WHERE status = 'ACKNOWLEDGED'
        """
    )

    op.drop_constraint(
        "ck_alert_confirmed_fields_pair",
        "alert",
        type_="check",
    )
    op.drop_constraint(
        "ck_alert_acknowledged_fields_pair",
        "alert",
        type_="check",
    )
    op.drop_constraint(
        "ck_alert_status",
        "alert",
        type_="check",
    )

    op.drop_constraint(
        "alert_confirmed_by_fkey",
        "alert",
        type_="foreignkey",
    )
    op.drop_constraint(
        "alert_acknowledged_by_fkey",
        "alert",
        type_="foreignkey",
    )

    op.drop_column("alert", "confirmed_at")
    op.drop_column("alert", "confirmed_by")
    op.drop_column("alert", "acknowledged_at")
    op.drop_column("alert", "acknowledged_by")
