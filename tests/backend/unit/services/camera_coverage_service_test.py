from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.camera_coverage import MAX_CAMERA_COVERAGE_RANGE_METRES
from app.models.audit_log import AuditAction, TargetEntity
from app.models.camera import Camera
from app.models.camera_coverage import CameraCoverage
from app.models.property import Property
from app.schemas.camera_coverage import CameraCoverageInput
from app.services.camera_coverage_service import (
    delete_camera_coverage_handler,
    get_camera_coverage_handler,
    upsert_camera_coverage_handler,
)


CAMERA_ID = UUID("40000000-0000-0000-0000-000000000001")
COVERAGE_ID = UUID("50000000-0000-0000-0000-000000000001")
USER_ID = UUID("11111111-1111-1111-1111-111111111111")

PROPERTY_LATITUDE = -25.747000
PROPERTY_LONGITUDE = 28.229000

CLAIMS = {
    "id": str(USER_ID),
    "sub": "test-user",
}


def make_payload(
    *,
    origin_latitude: float = PROPERTY_LATITUDE,
    origin_longitude: float = PROPERTY_LONGITUDE,
    bearing: float = 90.0,
    angle: float = 60.0,
    range_metres: float = 100.0,
) -> CameraCoverageInput:
    return CameraCoverageInput(
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        coverage_bearing_degrees=bearing,
        coverage_angle_degrees=angle,
        coverage_range_metres=range_metres,
    )


def make_camera() -> MagicMock:
    camera = MagicMock(spec=Camera)
    camera.id = CAMERA_ID
    camera.property_id = UUID("60000000-0000-0000-0000-000000000001")
    return camera


def make_property(
    *,
    latitude: float | None = PROPERTY_LATITUDE,
    longitude: float | None = PROPERTY_LONGITUDE,
) -> MagicMock:
    property_obj = MagicMock(spec=Property)
    property_obj.id = UUID("60000000-0000-0000-0000-000000000001")
    property_obj.latitude = latitude
    property_obj.longitude = longitude
    return property_obj


def make_coverage(
    *,
    coverage_id: UUID = COVERAGE_ID,
    camera_id: UUID = CAMERA_ID,
) -> CameraCoverage:
    coverage = CameraCoverage(
        camera_id=camera_id,
        origin_latitude=PROPERTY_LATITUDE,
        origin_longitude=PROPERTY_LONGITUDE,
        coverage_bearing_degrees=90.0,
        coverage_angle_degrees=60.0,
        coverage_range_metres=100.0,
    )
    coverage.id = coverage_id
    return coverage


def make_db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock()
    db.scalar = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def audit_log_mock() -> AsyncMock:
    with patch(
        "app.services.camera_coverage_service.create_audit_log_item",
        new_callable=AsyncMock,
    ) as mock_audit_log:
        yield mock_audit_log


@pytest.mark.asyncio
async def test_get_camera_coverage_returns_none_when_camera_has_no_coverage():
    camera = make_camera()
    db = make_db()
    db.scalar.side_effect = [camera, None]

    result = await get_camera_coverage_handler(
        camera_id=CAMERA_ID,
        db=db,
        claims=CLAIMS,
    )

    assert result is None
    assert db.scalar.await_count == 2


@pytest.mark.asyncio
async def test_get_camera_coverage_returns_saved_coverage():
    camera = make_camera()
    coverage = make_coverage()

    db = make_db()
    db.scalar.side_effect = [camera, coverage]

    result = await get_camera_coverage_handler(
        camera_id=CAMERA_ID,
        db=db,
        claims=CLAIMS,
    )

    assert result is not None
    assert result.id == COVERAGE_ID
    assert result.camera_id == CAMERA_ID
    assert result.origin_latitude == PROPERTY_LATITUDE
    assert result.origin_longitude == PROPERTY_LONGITUDE
    assert result.coverage_bearing_degrees == 90.0
    assert result.coverage_angle_degrees == 60.0
    assert result.coverage_range_metres == 100.0

    assert len(result.polygon) == 27
    assert result.polygon[0] == [
        PROPERTY_LATITUDE,
        PROPERTY_LONGITUDE,
    ]
    assert result.polygon[-1] == [
        PROPERTY_LATITUDE,
        PROPERTY_LONGITUDE,
    ]
    assert result.polygon[0] == [
        PROPERTY_LATITUDE,
        PROPERTY_LONGITUDE,
    ]


@pytest.mark.asyncio
async def test_get_camera_coverage_raises_when_camera_does_not_exist():
    db = make_db()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_camera_coverage_handler(
            camera_id=CAMERA_ID,
            db=db,
            claims=CLAIMS,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Camera not found"


@pytest.mark.asyncio
async def test_upsert_camera_coverage_creates_new_coverage(
    audit_log_mock: AsyncMock,
):
    camera = make_camera()
    property_obj = make_property()
    payload = make_payload()

    joined_result = MagicMock()
    joined_result.one_or_none.return_value = (camera, property_obj)

    db = make_db()
    db.execute.return_value = joined_result
    db.scalar.return_value = None

    async def refresh_created_coverage(coverage: CameraCoverage) -> None:
        coverage.id = COVERAGE_ID

    db.refresh.side_effect = refresh_created_coverage

    result = await upsert_camera_coverage_handler(
        camera_id=CAMERA_ID,
        payload=payload,
        db=db,
        claims=CLAIMS,
    )

    assert result.id == COVERAGE_ID
    assert result.camera_id == CAMERA_ID
    assert result.origin_latitude == payload.origin_latitude
    assert result.origin_longitude == payload.origin_longitude
    assert result.coverage_bearing_degrees == payload.coverage_bearing_degrees
    assert result.coverage_angle_degrees == payload.coverage_angle_degrees
    assert result.coverage_range_metres == payload.coverage_range_metres

    db.add.assert_called_once()
    created_coverage = db.add.call_args.args[0]

    assert isinstance(created_coverage, CameraCoverage)
    assert created_coverage.camera_id == CAMERA_ID
    assert created_coverage.origin_latitude == payload.origin_latitude
    assert created_coverage.origin_longitude == payload.origin_longitude
    assert created_coverage.coverage_bearing_degrees == (
        payload.coverage_bearing_degrees
    )
    assert created_coverage.coverage_angle_degrees == (
        payload.coverage_angle_degrees
    )
    assert created_coverage.coverage_range_metres == (
        payload.coverage_range_metres
    )

    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(created_coverage)

    audit_log_mock.assert_awaited_once()
    audit_kwargs = audit_log_mock.await_args.kwargs

    assert audit_kwargs["db"] is db
    assert audit_kwargs["user_id"] == USER_ID
    assert audit_kwargs["action"] == AuditAction.CREATE
    assert audit_kwargs["target_entity_type"] == TargetEntity.CAMERA
    assert audit_kwargs["target_entity_id"] == CAMERA_ID
    assert audit_kwargs["old_values"] is None
    assert audit_kwargs["new_values"] == payload.model_dump(mode="json")


@pytest.mark.asyncio
async def test_upsert_camera_coverage_updates_existing_coverage(
    audit_log_mock: AsyncMock,
):
    camera = make_camera()
    property_obj = make_property()
    existing_coverage = make_coverage()

    payload = make_payload(
        origin_latitude=PROPERTY_LATITUDE + 0.0001,
        origin_longitude=PROPERTY_LONGITUDE + 0.0001,
        bearing=180.0,
        angle=90.0,
        range_metres=150.0,
    )

    joined_result = MagicMock()
    joined_result.one_or_none.return_value = (camera, property_obj)

    db = make_db()
    db.execute.return_value = joined_result
    db.scalar.return_value = existing_coverage

    result = await upsert_camera_coverage_handler(
        camera_id=CAMERA_ID,
        payload=payload,
        db=db,
        claims=CLAIMS,
    )

    assert result.id == COVERAGE_ID
    assert result.camera_id == CAMERA_ID
    assert result.coverage_bearing_degrees == 180.0
    assert result.coverage_angle_degrees == 90.0
    assert result.coverage_range_metres == 150.0

    db.add.assert_not_called()
    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()

    audit_log_mock.assert_awaited_once()
    audit_kwargs = audit_log_mock.await_args.kwargs

    assert audit_kwargs["action"] == AuditAction.UPDATE
    assert audit_kwargs["target_entity_type"] == TargetEntity.CAMERA
    assert audit_kwargs["target_entity_id"] == CAMERA_ID
    assert audit_kwargs["old_values"] == {
        "origin_latitude": PROPERTY_LATITUDE,
        "origin_longitude": PROPERTY_LONGITUDE,
        "coverage_bearing_degrees": 90.0,
        "coverage_angle_degrees": 60.0,
        "coverage_range_metres": 100.0,
    }
    assert audit_kwargs["new_values"] == payload.model_dump(mode="json")


@pytest.mark.asyncio
async def test_upsert_camera_coverage_raises_when_camera_does_not_exist():
    payload = make_payload()

    joined_result = MagicMock()
    joined_result.one_or_none.return_value = None

    db = make_db()
    db.execute.return_value = joined_result

    with pytest.raises(HTTPException) as exc_info:
        await upsert_camera_coverage_handler(
            camera_id=CAMERA_ID,
            payload=payload,
            db=db,
            claims=CLAIMS,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Camera not found"
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_upsert_camera_coverage_rejects_property_without_coordinates():
    camera = make_camera()
    property_obj = make_property(latitude=None, longitude=None)
    payload = make_payload()

    joined_result = MagicMock()
    joined_result.one_or_none.return_value = (camera, property_obj)

    db = make_db()
    db.execute.return_value = joined_result

    with pytest.raises(HTTPException) as exc_info:
        await upsert_camera_coverage_handler(
            camera_id=CAMERA_ID,
            payload=payload,
            db=db,
            claims=CLAIMS,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "The property must have valid coordinates before a camera POV "
        "can be configured"
    )
    db.scalar.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_upsert_camera_coverage_rejects_origin_more_than_100_metres_away():
    camera = make_camera()
    property_obj = make_property()

    payload = make_payload(
        origin_latitude=PROPERTY_LATITUDE + 0.002,
        origin_longitude=PROPERTY_LONGITUDE,
    )

    joined_result = MagicMock()
    joined_result.one_or_none.return_value = (camera, property_obj)

    db = make_db()
    db.execute.return_value = joined_result

    with pytest.raises(HTTPException) as exc_info:
        await upsert_camera_coverage_handler(
            camera_id=CAMERA_ID,
            payload=payload,
            db=db,
            claims=CLAIMS,
        )

    assert exc_info.value.status_code == 400
    assert "within 100 metres of the property" in exc_info.value.detail
    db.scalar.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_camera_coverage_deletes_existing_coverage():
    camera = make_camera()
    coverage = make_coverage()

    db = make_db()
    db.scalar.side_effect = [camera, coverage]

    await delete_camera_coverage_handler(
        camera_id=CAMERA_ID,
        db=db,
        claims=CLAIMS,
    )

    db.delete.assert_awaited_once_with(coverage)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_camera_coverage_is_idempotent_when_coverage_is_missing():
    camera = make_camera()

    db = make_db()
    db.scalar.side_effect = [camera, None]

    result = await delete_camera_coverage_handler(
        camera_id=CAMERA_ID,
        db=db,
        claims=CLAIMS,
    )

    assert result is None
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_camera_coverage_raises_when_camera_does_not_exist():
    db = make_db()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await delete_camera_coverage_handler(
            camera_id=CAMERA_ID,
            db=db,
            claims=CLAIMS,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Camera not found"
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("origin_latitude", -90.1),
        ("origin_latitude", 90.1),
        ("origin_longitude", -180.1),
        ("origin_longitude", 180.1),
        ("coverage_bearing_degrees", -0.1),
        ("coverage_bearing_degrees", 360.0),
        ("coverage_angle_degrees", 0.99),
        ("coverage_angle_degrees", 180.1),
        ("coverage_range_metres", 0.99),
        (
            "coverage_range_metres",
            MAX_CAMERA_COVERAGE_RANGE_METRES + 0.1,
        ),
    ],
)
def test_camera_coverage_input_rejects_invalid_values(
    field_name: str,
    invalid_value: float,
):
    values = make_payload().model_dump()
    values[field_name] = invalid_value

    with pytest.raises(ValidationError):
        CameraCoverageInput(**values)


def test_camera_coverage_input_accepts_validation_boundaries():
    payload = CameraCoverageInput(
        origin_latitude=-90.0,
        origin_longitude=180.0,
        coverage_bearing_degrees=0.0,
        coverage_angle_degrees=180.0,
        coverage_range_metres=MAX_CAMERA_COVERAGE_RANGE_METRES,
    )

    assert payload.origin_latitude == -90.0
    assert payload.origin_longitude == 180.0
    assert payload.coverage_bearing_degrees == 0.0
    assert payload.coverage_angle_degrees == 180.0
    assert payload.coverage_range_metres == (
        MAX_CAMERA_COVERAGE_RANGE_METRES
    )