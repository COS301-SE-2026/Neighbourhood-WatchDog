"""add nullable latitude and longitude to property

Revision ID: e8c4a2b1d6f0
Revises: d1650db93f25
Create Date: 2026-09-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e8c4a2b1d6f0"
down_revision: Union[str, Sequence[str], None] = "d1650db93f25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "property", 
        sa.Column("latitude", sa.Float(), nullable=True)
    )
    op.add_column(
        "property", 
        sa.Column("longitude", sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("property", "longitude")
    op.drop_column("property", "latitude")