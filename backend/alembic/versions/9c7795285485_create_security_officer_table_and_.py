"""create security officer table and restore heartbeat index

Revision ID: 9c7795285485
Revises: ad46ced5f06b
Create Date: 2026-09-15 08:31:07.805975

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c7795285485'
down_revision: Union[str, Sequence[str], None] = 'ad46ced5f06b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    availability_enum = postgresql.ENUM(
        "AVAILABLE",
        "BUSY",
        "UNAVAILABLE",
        name="availability_status",
    )
    availability_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "security_officer",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "neighbourhood_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "availability_status",
            postgresql.ENUM(
                "AVAILABLE",
                "BUSY",
                "UNAVAILABLE",
                name="availability_status",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["neighbourhood_user_id"],
            ["neighbourhood_user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("neighbourhood_user_id"),
    )

    op.create_index(
        "ix_security_officer_lookup",
        "security_officer",
        [
            "neighbourhood_user_id",
            "availability_status",
        ],
        unique=False,
    )

    # ad46ced5f06b incorrectly removed this index.
    op.create_index(
        "ix_edge_agent_credentials_property_last_seen",
        "edge_agent_credential",
        ["property_id", "last_seen_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_edge_agent_credentials_property_last_seen",
        table_name="edge_agent_credential",
    )

    op.drop_index(
        "ix_security_officer_lookup",
        table_name="security_officer",
    )

    op.drop_table("security_officer")

    availability_enum = postgresql.ENUM(
        "AVAILABLE",
        "BUSY",
        "UNAVAILABLE",
        name="availability_status",
    )
    availability_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
