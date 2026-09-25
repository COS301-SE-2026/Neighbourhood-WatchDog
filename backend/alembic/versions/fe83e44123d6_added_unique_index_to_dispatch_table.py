"""added unique index to dispatch table

Revision ID: fe83e44123d6
Revises: 165eca849760
Create Date: 2026-09-25 19:59:30.715873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe83e44123d6'
down_revision: Union[str, Sequence[str], None] = '81d08417eb88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'uq_dispatch_one_accepted_per_alert',
        'dispatch',
        ['alert_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACCEPTED'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        'uq_dispatch_one_accepted_per_alert',
        table_name='dispatch',
        postgresql_where=sa.text("status = 'ACCEPTED'"),
    )