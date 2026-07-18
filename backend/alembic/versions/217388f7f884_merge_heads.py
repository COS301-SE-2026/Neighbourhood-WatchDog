"""merge heads

Revision ID: 217388f7f884
Revises: 24ebe8a57883, ed7933c51c73
Create Date: 2026-07-18 14:19:56.580950

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '217388f7f884'
down_revision: Union[str, Sequence[str], None] = ('24ebe8a57883', 'ed7933c51c73')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
