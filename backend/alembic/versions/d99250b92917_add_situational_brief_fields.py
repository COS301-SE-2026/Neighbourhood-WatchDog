"""add situational brief fields"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd99250b92917'
down_revision: Union[str, Sequence[str], None] = "4111ccc9e82c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tracking_subject",
        sa.Column(
            "brief_generated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tracking_subject",
        sa.Column(
            "brief_trigger",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "tracking_subject",
        sa.Column(
            "brief_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("tracking_subject", "brief_data")
    op.drop_column("tracking_subject", "brief_trigger")
    op.drop_column("tracking_subject", "brief_generated_at")