"""merge heads

Revision ID: 5191c458d61f
Revises: 6e47defa1510, fe83e44123d6
Create Date: 2026-09-26 21:37:13.536706

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '5191c458d61f'
down_revision: Union[str, Sequence[str], None] = ('6e47defa1510', 'fe83e44123d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
