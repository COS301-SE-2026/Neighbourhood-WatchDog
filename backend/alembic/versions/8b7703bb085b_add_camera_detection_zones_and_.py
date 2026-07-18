"""add camera detection zones and confidence threshold

Revision ID: 8b7703bb085b
Revises: 919661e27f6e
Create Date: 2026-07-02 08:36:10.417020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b7703bb085b'
down_revision: Union[str, Sequence[str], None] = '919661e27f6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'camera' in tables:
        existing = {c['name'] for c in inspector.get_columns('camera')}
        if 'confidence_threshold' not in existing:
            op.add_column('camera', sa.Column('confidence_threshold', sa.Float(), server_default='0.5', nullable=False))

    if 'users' in tables:
        existing = {c['name'] for c in inspector.get_columns('users')}
        if 'first_name' not in existing:
            op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
        if 'last_name' not in existing:
            op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
        if 'neighbourhood_id' not in existing:
            op.add_column('users', sa.Column('neighbourhood_id', sa.UUID(), nullable=True))
            op.create_foreign_key(None, 'users', 'neighbourhood', ['neighbourhood_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'users' in tables:
        existing = {c['name'] for c in inspector.get_columns('users')}
        if 'neighbourhood_id' in existing:
            op.drop_constraint(None, 'users', type_='foreignkey')
            op.drop_column('users', 'neighbourhood_id')
        if 'last_name' in existing:
            op.drop_column('users', 'last_name')
        if 'first_name' in existing:
            op.drop_column('users', 'first_name')

    if 'camera' in tables:
        existing = {c['name'] for c in inspector.get_columns('camera')}
        if 'confidence_threshold' in existing:
            op.drop_column('camera', 'confidence_threshold')