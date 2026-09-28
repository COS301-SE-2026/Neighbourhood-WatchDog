"""restore clip_s3_key on tracking_sighting

Revision ID: 3edaed50faf0
Revises: 5191c458d61f
Create Date: 2026-09-28 09:53:25.899832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3edaed50faf0'
down_revision: Union[str, Sequence[str], None] = '5191c458d61f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _existing_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_columns("tracking_sighting")} 

def upgrade() -> None:
    """Upgrade schema."""
    cols = _existing_columns()
    if "clip_s3_key" not in cols:
        op.add_column(
            "tracking_sighting",
            sa.Column("clip_s3_key", sa.String(length=512), nullable=True)
        )
    if "clip_expires_at" not in cols:
        op.add_column(
            "tracking_sighting",
            sa.Column("clip_expires_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    cols = _existing_columns()
    if "clip_expires_at" in cols:
        op.drop_column("tracking_sighting", "clip_expires_at")
    if "clip_s3_key" in cols:
        op.drop_column("tracking_sighting", "clip_s3_key")