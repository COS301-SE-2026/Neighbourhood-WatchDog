"""merge migration heads

Revision ID: 165eca849760
Revises: 8940966428e1, 06dddc13595a
Create Date: 2026-09-24 16:29:31.998729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '165eca849760'
down_revision: Union[str, Sequence[str], None] = ('8940966428e1', '06dddc13595a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
