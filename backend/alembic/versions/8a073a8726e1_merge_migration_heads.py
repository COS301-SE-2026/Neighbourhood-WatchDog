"""merge migration heads

Revision ID: 8a073a8726e1
Revises: de4de5897f72, f4098eeef2e2
Create Date: 2026-07-29 17:56:23.230318

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '8a073a8726e1'
down_revision: Union[str, Sequence[str], None] = ('de4de5897f72', 'f4098eeef2e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
