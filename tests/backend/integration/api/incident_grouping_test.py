import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.camera import Camera, CameraVisibilityEnum
from app.models.incident import Incident
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_user import (
    NeighbourhoodRole,
    NeighbourhoodUser,
)
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.user import User, UserRole
from app.schemas.alert import CreateInternalAlertRequest
from app.services.alert_service import (
    create_alert_for_agent_handler,
)


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def grouping_camera():
    neighbourhood_id = uuid.uuid4()
    property_id = uuid.uuid4()
    camera_id = uuid.uuid4()
    second_camera_id = uuid.uuid4()
    user_id = uuid.uuid4()

    neighbourhood = Neighbourhood(
        id=neighbourhood_id,
        name=f"Grouping Test Neighbourhood {uuid.uuid4()}",
        location="Grouping Test Location",
        join_code=f"GROUP-{uuid.uuid4()}",
    )

    property_obj = Property(
        id=property_id,
        neighbourhood_id=neighbourhood_id,
        address="Grouping Test Address",
        latitude=-25.754,
        longitude=28.231,
        property_type=PropertyTypeEnum.PRIVATE,
    )

    camera = Camera(
        id=camera_id,
        property_id=property_id,
        name="Grouping Test Camera",
        location="Grouping Test Location",
        rtsp_url="rtsp://grouping-test-camera",
        visibility=CameraVisibilityEnum.PRIVATE,
        enabled=True,
    )

    second_camera = Camera(
        id=second_camera_id,
        property_id=property_id,
        name="Grouping Test Camera Two",
        location="Grouping Test Location Two",
        rtsp_url="rtsp://grouping-test-camera-two",
        visibility=CameraVisibilityEnum.PRIVATE,
        enabled=True,
    )

    user = User(
        id=user_id,
        email=f"grouping-user-{uuid.uuid4()}@example.com",
        cognito_sub=f"grouping-user-{uuid.uuid4()}",
        first_name="Grouping",
        last_name="User",
        system_role=UserRole.RESIDENT,
    )

    membership = NeighbourhoodUser(
        user_id=user_id,
        neighbourhood_id=neighbourhood_id,
        role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
    )

    property_membership = PropertyUser(
        user_id=user_id,
        property_id=property_id,
        is_admin=True,
    )

    async with SessionLocal() as db:
        db.add_all(
            [
                neighbourhood,
                property_obj,
                camera,
                second_camera,
                user,
                membership,
                property_membership,
            ]
        )
        await db.commit()

    data = {
        "neighbourhood_id": neighbourhood_id,
        "property_id": property_id,
        "camera_id": camera_id,
        "second_camera_id": second_camera_id,
        "user_id": user_id,
        "camera": camera,
    }

    try:
        yield data
    finally:
        async with SessionLocal() as db:
            incident_result = await db.execute(
                select(Alert.incident_id).where(
                    Alert.camera_id.in_([camera_id, second_camera_id])
                )
            )

            incident_ids = {
                incident_id
                for incident_id in incident_result.scalars().all()
                if incident_id is not None
            }

            await db.execute(
                delete(Alert).where(
                    Alert.camera_id.in_([camera_id, second_camera_id])
                )
            )

            if incident_ids:
                await db.execute(
                    delete(Incident).where(
                        Incident.id.in_(incident_ids)
                    )
                )

            await db.execute(
                delete(PropertyUser).where(
                    PropertyUser.user_id == user_id,
                    PropertyUser.property_id == property_id,
                )
            )

            await db.execute(
                delete(NeighbourhoodUser).where(
                    NeighbourhoodUser.user_id == user_id,
                    NeighbourhoodUser.neighbourhood_id
                    == neighbourhood_id,
                )
            )

            await db.execute(
                delete(Camera).where(
                    Camera.id.in_([camera_id, second_camera_id])
                )
            )

            await db.execute(
                delete(Property).where(Property.id == property_id)
            )

            await db.execute(
                delete(User).where(User.id == user_id)
            )

            await db.execute(
                delete(Neighbourhood).where(
                    Neighbourhood.id == neighbourhood_id
                )
            )

            await db.commit()


def make_weapon_request(
    camera_id: uuid.UUID,
    timestamp: datetime,
) -> CreateInternalAlertRequest:
    return CreateInternalAlertRequest(
        camera_id=str(camera_id),
        detection_type="WEAPON_DETECTED",
        confidence_score=0.95,
        frame_timestamp=timestamp.isoformat(),
        thumbnail_url=None,
        local_track_id=None,
    )




def make_tracked_request(
    camera_id: uuid.UUID,
    timestamp: datetime,
    detection_type: str,
    local_track_id: int,
    embedding: list[float],
) -> CreateInternalAlertRequest:
    return CreateInternalAlertRequest(
        camera_id=str(camera_id),
        detection_type=detection_type,
        confidence_score=0.95,
        frame_timestamp=timestamp.isoformat(),
        thumbnail_url=None,
        local_track_id=local_track_id,
        appearance_embedding=embedding,
        embedding_model="grouping-test-model",
    )


async def create_alert_with_session(**kwargs):
    async with SessionLocal() as db:
        return await create_alert_for_agent_handler(db=db, **kwargs)


def make_notification_policy():
    policy = SimpleNamespace()
    policy.notify = AsyncMock()
    return policy


@pytest.mark.asyncio
async def test_concurrent_weapon_detections_create_one_alert(
    grouping_camera,
):
    camera_id = grouping_camera["camera_id"]

    # Use the same timestamp so the test is about concurrency,
    # not out-of-order event timestamps.
    timestamp = datetime.now(timezone.utc).replace(
        microsecond=0
    )

    first_request = make_weapon_request(camera_id, timestamp)
    second_request = make_weapon_request(camera_id, timestamp)

    credential = SimpleNamespace(
        property_id=grouping_camera["property_id"],
    )

    notification_policy = make_notification_policy()

    async with SessionLocal() as first_db, SessionLocal() as second_db:
        with patch(
            "app.services.alert_service.NotificationPolicyFactory.get",
            new=Mock(return_value=notification_policy),
        ):
            first_result, second_result = await asyncio.gather(
                create_alert_for_agent_handler(
                    body=first_request,
                    db=first_db,
                    credential=credential,
                    generate_brief=False,
                ),
                create_alert_for_agent_handler(
                    body=second_request,
                    db=second_db,
                    credential=credential,
                    generate_brief=False,
                ),
            )

    assert {first_result.is_new_alert, second_result.is_new_alert} == {
        True,
        False,
    }

    assert first_result.alert_id == second_result.alert_id

    async with SessionLocal() as verify_db:
        alert_count_result = await verify_db.execute(
            select(func.count())
            .select_from(Alert)
            .where(Alert.camera_id == camera_id)
        )

        incident_count_result = await verify_db.execute(
            select(func.count())
            .select_from(Incident)
            .join(Alert, Alert.incident_id == Incident.id)
            .where(Alert.camera_id == camera_id)
        )

        assert alert_count_result.scalar_one() == 1
        assert incident_count_result.scalar_one() == 1


@pytest.mark.asyncio
async def test_detection_after_resolved_alert_creates_new_alert(
    grouping_camera,
):
    camera_id = grouping_camera["camera_id"]

    timestamp = datetime.now(timezone.utc).replace(
        microsecond=0
    )

    credential = SimpleNamespace(
        property_id=grouping_camera["property_id"],
    )

    notification_policy = make_notification_policy()

    with patch(
        "app.services.alert_service.NotificationPolicyFactory.get",
        new=Mock(return_value=notification_policy),
    ):
        async with SessionLocal() as first_db:
            first_result = await create_alert_for_agent_handler(
                body=make_weapon_request(camera_id, timestamp),
                db=first_db,
                credential=credential,
                generate_brief=False,
            )

        async with SessionLocal() as update_db:
            alert = await update_db.get(
                Alert,
                first_result.alert_id,
            )

            assert alert is not None

            alert.status = "RESOLVED"
            alert.resolved_by = grouping_camera["user_id"]
            alert.resolved_at = timestamp
            await update_db.commit()

        async with SessionLocal() as second_db:
            second_result = await create_alert_for_agent_handler(
                body=make_weapon_request(camera_id, timestamp),
                db=second_db,
                credential=credential,
                generate_brief=False,
            )

    assert first_result.is_new_alert is True
    assert second_result.is_new_alert is True
    assert first_result.alert_id != second_result.alert_id


@pytest.mark.asyncio
async def test_confirmed_alert_remains_groupable(
    grouping_camera,
):
    camera_id = grouping_camera["camera_id"]

    timestamp = datetime.now(timezone.utc).replace(
        microsecond=0
    )

    credential = SimpleNamespace(
        property_id=grouping_camera["property_id"],
    )

    notification_policy = make_notification_policy()

    with patch(
        "app.services.alert_service.NotificationPolicyFactory.get",
        new=Mock(return_value=notification_policy),
    ):
        async with SessionLocal() as first_db:
            first_result = await create_alert_for_agent_handler(
                body=make_weapon_request(camera_id, timestamp),
                db=first_db,
                credential=credential,
                generate_brief=False,
            )

        async with SessionLocal() as update_db:
            alert = await update_db.get(
                Alert,
                first_result.alert_id,
            )

            assert alert is not None

            alert.status = "CONFIRMED"
            await update_db.commit()

        async with SessionLocal() as second_db:
            second_result = await create_alert_for_agent_handler(
                body=make_weapon_request(camera_id, timestamp),
                db=second_db,
                credential=credential,
                generate_brief=False,
            )

    assert first_result.is_new_alert is True
    assert second_result.is_new_alert is False
    assert first_result.alert_id == second_result.alert_id


@pytest.mark.asyncio
async def test_cross_camera_grouping_accuracy_meets_75_percent(
    grouping_camera,
):
    """Evaluate four labelled same-person/impostor cross-camera sightings."""
    first_camera = grouping_camera["camera_id"]
    second_camera = grouping_camera["second_camera_id"]
    timestamp = datetime.now(timezone.utc).replace(microsecond=0)
    credential = SimpleNamespace(property_id=grouping_camera["property_id"])
    notification_policy = make_notification_policy()

    def vector(index: int, sign: float = 1.0) -> list[float]:
        values = [0.0] * 1280
        values[index] = sign
        return values

    seed_embeddings = [vector(0), vector(1)]
    seed_incidents = []
    with patch(
        "app.services.alert_service.NotificationPolicyFactory.get",
        new=Mock(return_value=notification_policy),
    ):
        for index, embedding in enumerate(seed_embeddings):
            result = await create_alert_with_session(
                body=make_tracked_request(
                    first_camera,
                    timestamp,
                    "WEAPON_DETECTED",
                    100 + index,
                    embedding,
                ),
                credential=credential,
                generate_brief=False,
            )
            async with SessionLocal() as verify_db:
                alert = await verify_db.get(Alert, result.alert_id)
                assert alert is not None and alert.incident_id is not None
                seed_incidents.append(alert.incident_id)

        known_incidents = set(seed_incidents)
        labelled_queries = [
            # Positive: same person, different camera and detection category.
            (vector(0), "HUMAN_PRESENCE", seed_incidents[0]),
            (vector(1), "LOITERING", seed_incidents[1]),
            # Negative: orthogonal or opposite identity must start a new group.
            (vector(2), "HUMAN_PRESENCE", None),
            (vector(0, -1.0), "PERIMETER_SCAN", None),
        ]

        correct = 0
        for index, (embedding, detection_type, expected_incident_id) in enumerate(
            labelled_queries
        ):
            result = await create_alert_with_session(
                body=make_tracked_request(
                    second_camera,
                    timestamp + timedelta(seconds=index + 1),
                    detection_type,
                    200 + index,
                    embedding,
                ),
                credential=credential,
                generate_brief=False,
            )
            async with SessionLocal() as verify_db:
                alert = await verify_db.get(Alert, result.alert_id)
                assert alert is not None and alert.incident_id is not None
                if expected_incident_id is None:
                    correct += alert.incident_id not in known_incidents
                else:
                    correct += alert.incident_id == expected_incident_id
                known_incidents.add(alert.incident_id)

    accuracy = correct / len(labelled_queries)
    assert accuracy >= 0.75, f"cross-camera grouping accuracy was {accuracy:.0%}"
