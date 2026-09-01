"""add last_seen_at to edge agent credentials"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c9d1e2b4"
down_revision: Union[str, Sequence[str], None] = "f29ba2d230ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "edge_agent_credential",
        sa.Column(
            "last_seen_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True
        )
    )

    op.create_index(
        "ix_edge_agent_credentials_property_last_seen",
        "edge_agent_credential",
        ["property_id", "last_seen_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_edge_agent_credentials_property_last_seen",
        table_name="edge_agent_credential"
    )

    op.drop_column(
        "edge_agent_credential",
        "last_seen_at"
    )