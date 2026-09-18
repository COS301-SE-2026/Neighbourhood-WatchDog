"""merge tracking and dev migration heads

Revision ID: 4111ccc9e82c
Revises: 0ca09c23ed0c, 240e5f7e480a
Create Date: 2026-09-18 15:21:26.162266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '4111ccc9e82c'
down_revision: Union[str, Sequence[str], None] = ('0ca09c23ed0c', '240e5f7e480a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
