from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.edge_agent_credentials import EdgeAgentCredential


HEARTBEAT_WRITE_INTERVAL_SECONDS = 10


async def record_edge_agent_heartbeat(credential: EdgeAgentCredential, db: AsyncSession) -> None:
    """Record that a valid, non-revoked Edge Agent reached the backend."""

    now = datetime.now(timezone.utc)

    if credential.last_seen_at is not None:
        elapsed_seconds = (now - credential.last_seen_at).total_seconds()

        if elapsed_seconds < HEARTBEAT_WRITE_INTERVAL_SECONDS:
            return

    credential.last_seen_at = now

    
    await db.commit()