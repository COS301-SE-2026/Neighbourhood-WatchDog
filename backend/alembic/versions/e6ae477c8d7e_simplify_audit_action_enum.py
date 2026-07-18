"""Simplify audit action enum

Revision ID: e6ae477c8d7e
Revises: 24ebe8a57883
Create Date: 2026-07-18 16:38:52.407978

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e6ae477c8d7e'
down_revision: Union[str, Sequence[str], None] = '24ebe8a57883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE audit_log ALTER COLUMN action TYPE text")
    op.execute("DROP TYPE auditaction")
    op.execute("CREATE TYPE auditaction AS ENUM ('CREATE', 'UPDATE', 'DELETE')")
    op.execute(
        "ALTER TABLE audit_log ALTER COLUMN action TYPE auditaction USING action::auditaction"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE audit_log ALTER COLUMN action TYPE text")
    op.execute("DROP TYPE auditaction")
    op.execute(
        "CREATE TYPE auditaction AS ENUM ("
        "'LOGIN', 'LOGOUT', 'REGISTER_CAMERA', 'DELETE_CAMERA', 'UPDTAE_ZONE_CONFIG', "
        "'UPDTAE_THRESHOLD', 'ACKNOWLEDGE_ALERT', 'RESOLVE_ALERT', 'VIEW_FOOTAGE', "
        "'CREATE_NEIGHBOURHOOD', 'JOIN_NEIGHBOURHOOD', 'UPDATE_RETENTION_POLICY', "
        "'REGISTER_ACCOUNT', 'UPDATE_CAMERA_VISIBILITY', 'CONFIGURE_ALERT_THRESHOLD'"
        ")"
    )
    op.execute("ALTER TABLE audit_log ALTER COLUMN action TYPE auditaction USING action::auditaction")
