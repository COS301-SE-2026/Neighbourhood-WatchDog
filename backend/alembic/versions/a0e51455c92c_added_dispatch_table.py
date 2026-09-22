"""added dispatch table

Revision ID: a0e51455c92c
Revises: d99250b92917
Create Date: 2026-09-21 21:47:02.151535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a0e51455c92c'
down_revision: Union[str, Sequence[str], None] = 'd99250b92917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('dispatch',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('alert_id', sa.UUID(), nullable=False),
    sa.Column('neighbourhood_id', sa.UUID(), nullable=True),
    sa.Column('officer_id', sa.UUID(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('distance', sa.Float(), nullable=True),
    sa.Column('eta', sa.Float(), nullable=True),
    sa.Column('workload', sa.Integer(), nullable=True),
    sa.Column('officer_availability', postgresql.ENUM('AVAILABLE', 'BUSY', 'UNAVAILABLE', name='availability_status', create_type=False), nullable=True),
    sa.Column('officer_location_updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('SELECTED', 'PENDING', 'QUEUED', 'NOTIFIED', 'ACCEPTED', 'DECLINED', 'TIMED_OUT', 'NO_CANDIDATE', name='dispatch_status'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('notified_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('responded_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'NO_CANDIDATE' AND officer_id IS NULL) OR status IN ('ACCEPTED', 'DECLINED', 'TIMED_OUT') OR officer_id IS NOT NULL", name='ck_dispatch_officer_matches_status'),
    sa.CheckConstraint('rank IS NULL OR rank > 0', name='ck_dispatch_rank_positive'),
    sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['neighbourhood_id'], ['neighbourhood.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['officer_id'], ['security_officer.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dispatch_alert_rank', 'dispatch', ['alert_id', 'rank'], unique=False)
    op.create_index('ix_dispatch_neighbourhood', 'dispatch', ['neighbourhood_id'], unique=False)
    op.create_index('ix_dispatch_neighbourhood_status', 'dispatch', ['neighbourhood_id', 'status'], unique=False)
    op.create_index('ix_dispatch_officer', 'dispatch', ['officer_id'], unique=False)
    op.create_index('uq_dispatch_alert_officer', 'dispatch', ['alert_id', 'officer_id'], unique=True, postgresql_where=sa.text('officer_id IS NOT NULL'))
    op.create_index('uq_dispatch_one_selected_per_alert', 'dispatch', ['alert_id'], unique=True, postgresql_where=sa.text("status = 'SELECTED'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_dispatch_one_selected_per_alert', table_name='dispatch', postgresql_where=sa.text("status = 'SELECTED'"))
    op.drop_index('uq_dispatch_alert_officer', table_name='dispatch', postgresql_where=sa.text('officer_id IS NOT NULL'))
    op.drop_index('ix_dispatch_officer', table_name='dispatch')
    op.drop_index('ix_dispatch_neighbourhood_status', table_name='dispatch')
    op.drop_index('ix_dispatch_neighbourhood', table_name='dispatch')
    op.drop_index('ix_dispatch_alert_rank', table_name='dispatch')
    op.drop_table('dispatch')
    postgresql.ENUM(name='dispatch_status').drop(op.get_bind(), checkfirst=True)