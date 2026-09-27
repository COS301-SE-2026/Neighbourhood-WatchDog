"""add camera coverage

Revision ID: 9bc903d75aba
Revises: 165eca849760
Create Date: 2026-09-25 12:54:47.571238

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9bc903d75aba"
down_revision: Union[str, Sequence[str], None] = "165eca849760"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the geographic camera coverage table."""
    op.create_table(
        "camera_coverage",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "origin_latitude",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "origin_longitude",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "coverage_bearing_degrees",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "coverage_angle_degrees",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "coverage_range_metres",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "origin_latitude BETWEEN -90 AND 90",
            name="ck_camera_coverage_latitude",
        ),
        sa.CheckConstraint(
            "origin_longitude BETWEEN -180 AND 180",
            name="ck_camera_coverage_longitude",
        ),
        sa.CheckConstraint(
            "coverage_bearing_degrees >= 0 "
            "AND coverage_bearing_degrees < 360",
            name="ck_camera_coverage_bearing",
        ),
        sa.CheckConstraint(
            "coverage_angle_degrees BETWEEN 1 AND 180",
            name="ck_camera_coverage_angle",
        ),
        sa.CheckConstraint(
            "coverage_range_metres BETWEEN 1 AND 200",
            name="ck_camera_coverage_range",
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["camera.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "camera_id",
            name="uq_camera_coverage_camera_id",
        ),
    )


def downgrade() -> None:
    """Remove the geographic camera coverage table."""
    op.drop_table("camera_coverage")