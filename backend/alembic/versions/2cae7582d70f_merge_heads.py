"""merge heads

Revision ID: 2cae7582d70f
Revises: 3f0d5fabf71e, add_incident_grouping
Create Date: 2026-09-29 17:55:52.565385

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '2cae7582d70f'
down_revision: Union[str, Sequence[str], None] = ('3f0d5fabf71e', 'add_incident_grouping')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
