"""added fk and updated indexes

Revision ID: 3f0d5fabf71e
Revises: 05696974518c
Create Date: 2026-09-29 13:03:24.237571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f0d5fabf71e'
down_revision: Union[str, Sequence[str], None] = '05696974518c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('dispatch', sa.Column('triggering_sighting_id', sa.UUID(), nullable=True))
    op.drop_index('uq_dispatch_one_accepted_per_alert', table_name='dispatch')
    op.drop_index('uq_dispatch_one_selected_per_alert', table_name='dispatch')
    op.create_index('ix_dispatch_alert_round', 'dispatch', ['alert_id', 'triggering_sighting_id'], unique=False)
    op.create_index('uq_dispatch_one_accepted_per_round', 'dispatch', ['alert_id', sa.literal_column("COALESCE(triggering_sighting_id, '00000000-0000-0000-0000-000000000000'::uuid)")], unique=True, postgresql_where=sa.text("status = 'ACCEPTED'"))
    op.create_index('uq_dispatch_one_selected_per_round', 'dispatch', ['alert_id', sa.literal_column("COALESCE(triggering_sighting_id, '00000000-0000-0000-0000-000000000000'::uuid)")], unique=True, postgresql_where=sa.text("status = 'SELECTED'"))
    op.create_foreign_key('fk_dispatch_triggering_sighting_id_tracking_sighting', 'dispatch', 'tracking_sighting', ['triggering_sighting_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_dispatch_triggering_sighting_id_tracking_sighting', 'dispatch', type_='foreignkey')
    op.drop_index('uq_dispatch_one_selected_per_round', table_name='dispatch')
    op.drop_index('uq_dispatch_one_accepted_per_round', table_name='dispatch')
    op.drop_index('ix_dispatch_alert_round', table_name='dispatch')
    op.create_index('uq_dispatch_one_selected_per_alert', 'dispatch', ['alert_id'], unique=True, postgresql_where=sa.text("status = 'SELECTED'::dispatch_status"))
    op.create_index('uq_dispatch_one_accepted_per_alert', 'dispatch', ['alert_id'], unique=True, postgresql_where=sa.text("status = 'ACCEPTED'::dispatch_status"))
    op.drop_column('dispatch', 'triggering_sighting_id')