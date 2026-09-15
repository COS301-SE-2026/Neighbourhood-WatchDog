"""cascade property camera alert deletion

Revision ID: a57ec0c60e37
Revises: e8c4a2b1d6f0
Create Date: 2026-09-15 05:04:03.146499
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a57ec0c60e37"
down_revision: Union[str, Sequence[str], None] = "e8c4a2b1d6f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deletion behaviour to property relationships."""

    op.drop_constraint(
        "alert_camera_id_fkey",
        "alert",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "alert_camera_id_fkey",
        "alert",
        "camera",
        ["camera_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "camera_property_id_fkey",
        "camera",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "camera_property_id_fkey",
        "camera",
        "property",
        ["property_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "property_neighbourhood_id_fkey",
        "property",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "property_neighbourhood_id_fkey",
        "property",
        "neighbourhood",
        ["neighbourhood_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Restore the previous deletion behaviour."""

    op.drop_constraint(
        "property_neighbourhood_id_fkey",
        "property",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "property_neighbourhood_id_fkey",
        "property",
        "neighbourhood",
        ["neighbourhood_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "camera_property_id_fkey",
        "camera",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "camera_property_id_fkey",
        "camera",
        "property",
        ["property_id"],
        ["id"],
    )

    op.drop_constraint(
        "alert_camera_id_fkey",
        "alert",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "alert_camera_id_fkey",
        "alert",
        "camera",
        ["camera_id"],
        ["id"],
    )
