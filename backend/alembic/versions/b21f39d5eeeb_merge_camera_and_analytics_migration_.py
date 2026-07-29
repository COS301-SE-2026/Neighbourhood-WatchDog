"""merge camera and analytics migration heads

Revision ID: b21f39d5eeeb
Revises: f4098eeef2e2, de4de5897f72
Create Date: 2026-07-29 17:37:26.408180

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'b21f39d5eeeb'
down_revision: Union[str, Sequence[str], None] = ('f4098eeef2e2', 'de4de5897f72')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
