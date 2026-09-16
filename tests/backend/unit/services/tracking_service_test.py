from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.services.tracking_service import record_tracking_sighting


@pytest.mark.asyncio
async def test_http_exception_is_reraised():
    """
    Covers:

        except HTTPException:
            raise

    The original HTTPException should pass through unchanged.
    """

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
            match_confidence=1.5,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "match confidence must be between 0 and 1"


@pytest.mark.asyncio
async def test_integrity_error_is_converted_to_409():
    """
    Covers:

        except IntegrityError as exc:
            await db.rollback()
            logger.warning(...)
            raise HTTPException(status_code=409, ...)

    Forces the database execute operation to raise IntegrityError.
    """

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=IntegrityError(
            "duplicate",
            {},
            Exception("duplicate constraint"),
        )
    )
    db.rollback = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 409
    assert (
        exc.value.detail
        == "Tracking sighting could not be recorded"
    )

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_unexpected_exception_is_converted_to_500():
    """
    Covers:

        except Exception as exc:
            await db.rollback()
            logger.exception(...)
            raise HTTPException(status_code=500, ...)

    Forces an unexpected database error.
    """

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=RuntimeError("database connection failed")
    )
    db.rollback = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Failed to record tracking sighting"

    db.rollback.assert_awaited_once()


