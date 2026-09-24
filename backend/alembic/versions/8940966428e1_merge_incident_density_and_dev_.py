"""merge incident density and dev migration heads

Revision ID: 8940966428e1
Revises: 7532e7c9f37e, 549c343e8433
Create Date: 2026-09-24 14:30:17.552564

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '8940966428e1'
down_revision: Union[str, Sequence[str], None] = ('7532e7c9f37e', '549c343e8433')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
