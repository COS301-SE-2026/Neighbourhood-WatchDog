"""add neighbourhooduser target entity

Revision ID: d1650db93f25
Revises: a7f3c9d1e2b4
Create Date: 2026-09-02 07:20:20.822243

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "d1650db93f25"
down_revision = "a7f3c9d1e2b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE targetentity "
        "ADD VALUE IF NOT EXISTS 'NEIGHBOURHOODUSER'"
    )


def downgrade() -> None:
    # PostgreSQL does not safely support removing one enum value.
    pass
