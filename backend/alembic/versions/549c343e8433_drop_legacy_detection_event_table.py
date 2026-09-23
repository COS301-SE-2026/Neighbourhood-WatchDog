"""drop legacy detection_event table

Revision ID: 549c343e8433
Revises: 649bafafac38
Create Date: 2026-09-23 17:59:46.146073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '549c343e8433'
down_revision: Union[str, Sequence[str], None] = '649bafafac38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("detection_event")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "detection_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()")),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frame_timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("detection_type", sa.Enum("HUMAN_PRESENCE", "LOITERING", "PERIMETER_SCAN", "WEAPON_DETECTED", "FALL_DETECTED", name="detection_type"), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("thumbnail_url", sa.String(), nullable=True),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("clip_s3_key", sa.String(), nullable=True),
        sa.Column("clip_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="ck_confidence_score_range"),
        sa.ForeignKeyConstraint(["camera_id"], ["camera.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
