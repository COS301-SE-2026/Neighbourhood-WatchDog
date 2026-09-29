import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.alert import Alert, AlertStatus, DetectionType
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


pytestmark = pytest.mark.integration


def make_headers(user: User, role: NeighbourhoodRole) -> dict[str, str]:
    return {
        "Authorization": "Bearer test",
        "X-Mock-Sub": user.cognito_sub,
        "X-Mock-User-Id": str(user.id),
        "X-Mock-Role": role.value,
    }


@pytest_asyncio.fixture
async def incident_scenario():
    neighbourhood_id = uuid.uuid4()

    property_one_id = uuid.uuid4()
    property_two_id = uuid.uuid4()

    camera_one_id = uuid.uuid4()
    camera_two_id = uuid.uuid4()

    viewer_id = uuid.uuid4()
    officer_id = uuid.uuid4()
    outsider_id = uuid.uuid4()

    incident_weapon_id = uuid.uuid4()
    incident_human_id = uuid.uuid4()
    incident_fall_id = uuid.uuid4()
    incident_other_property_id = uuid.uuid4()

    alert_weapon_one_id = uuid.uuid4()
    alert_weapon_two_id = uuid.uuid4()
    alert_human_id = uuid.uuid4()
    alert_fall_id = uuid.uuid4()
    alert_other_property_id = uuid.uuid4()

    base_time = datetime.now(timezone.utc).replace(microsecond=0)

    neighbourhood = Neighbourhood(
        id=neighbourhood_id,
        name=f"Incident Test Neighbourhood {uuid.uuid4()}",
        location="Test Location",
        join_code=f"TEST-{uuid.uuid4()}",
    )

    property_one = Property(
        id=property_one_id,
        neighbourhood_id=neighbourhood_id,
        address="1 Test Street",
        latitude=-25.754,
        longitude=28.231,
        property_type=PropertyTypeEnum.PRIVATE,
    )

    property_two = Property(
        id=property_two_id,
        neighbourhood_id=neighbourhood_id,
        address="2 Test Street",
        latitude=-25.755,
        longitude=28.232,
        property_type=PropertyTypeEnum.PRIVATE,
    )

    camera_one = Camera(
        id=camera_one_id,
        property_id=property_one_id,
        name="Test Camera One",
        location="Front gate",
        rtsp_url="rtsp://test-camera-one",
        visibility=CameraVisibilityEnum.PRIVATE,
        enabled=True,
    )

    camera_two = Camera(
        id=camera_two_id,
        property_id=property_two_id,
        name="Test Camera Two",
        location="Back gate",
        rtsp_url="rtsp://test-camera-two",
        visibility=CameraVisibilityEnum.PRIVATE,
        enabled=True,
    )

    viewer = User(
        id=viewer_id,
        email=f"incident-viewer-{uuid.uuid4()}@example.com",
        cognito_sub=f"incident-viewer-{uuid.uuid4()}",
        first_name="Incident",
        last_name="Viewer",
        system_role=UserRole.RESIDENT,
    )

    officer = User(
        id=officer_id,
        email=f"incident-officer-{uuid.uuid4()}@example.com",
        cognito_sub=f"incident-officer-{uuid.uuid4()}",
        first_name="Incident",
        last_name="Officer",
        system_role=UserRole.SECURITY_OFFICER,
    )

    outsider = User(
        id=outsider_id,
        email=f"incident-outsider-{uuid.uuid4()}@example.com",
        cognito_sub=f"incident-outsider-{uuid.uuid4()}",
        first_name="Incident",
        last_name="Outsider",
        system_role=UserRole.RESIDENT,
    )

    viewer_membership = NeighbourhoodUser(
        user_id=viewer_id,
        neighbourhood_id=neighbourhood_id,
        role=NeighbourhoodRole.RESIDENT,
    )

    officer_membership = NeighbourhoodUser(
        user_id=officer_id,
        neighbourhood_id=neighbourhood_id,
        role=NeighbourhoodRole.SECURITY_OFFICER,
    )

    viewer_property_membership = PropertyUser(
        user_id=viewer_id,
        property_id=property_one_id,
        is_admin=False,
    )

    incident_weapon = Incident(
        id=incident_weapon_id,
        detection_type=DetectionType.WEAPON_DETECTED.value,
        started_at=base_time - timedelta(minutes=5),
        last_seen_at=base_time - timedelta(minutes=4),
    )

    incident_human = Incident(
        id=incident_human_id,
        detection_type=DetectionType.HUMAN_PRESENCE.value,
        started_at=base_time - timedelta(days=2),
        last_seen_at=base_time - timedelta(days=2) + timedelta(minutes=1),
    )

    incident_fall = Incident(
        id=incident_fall_id,
        detection_type=DetectionType.FALL_DETECTED.value,
        started_at=base_time - timedelta(minutes=2),
        last_seen_at=base_time - timedelta(minutes=2),
    )

    incident_other_property = Incident(
        id=incident_other_property_id,
        detection_type=DetectionType.WEAPON_DETECTED.value,
        started_at=base_time - timedelta(minutes=3),
        last_seen_at=base_time - timedelta(minutes=3),
    )

    alerts = [
        Alert(
            id=alert_weapon_one_id,
            camera_id=camera_one_id,
            incident_id=incident_weapon_id,
            frame_timestamp=base_time - timedelta(minutes=5),
            detection_type=DetectionType.WEAPON_DETECTED,
            confidence_score=0.95,
            processed=True,
            status=AlertStatus.OPEN.value,
        ),
        Alert(
            id=alert_weapon_two_id,
            camera_id=camera_one_id,
            incident_id=incident_weapon_id,
            frame_timestamp=base_time - timedelta(minutes=4),
            detection_type=DetectionType.WEAPON_DETECTED,
            confidence_score=0.97,
            processed=True,
            status=AlertStatus.ACKNOWLEDGED.value,
        ),
        Alert(
            id=alert_human_id,
            camera_id=camera_one_id,
            incident_id=incident_human_id,
            frame_timestamp=base_time - timedelta(days=2),
            detection_type=DetectionType.HUMAN_PRESENCE,
            confidence_score=0.90,
            processed=True,
            status=AlertStatus.OPEN.value,
        ),
        Alert(
            id=alert_fall_id,
            camera_id=camera_one_id,
            incident_id=incident_fall_id,
            frame_timestamp=base_time - timedelta(minutes=2),
            detection_type=DetectionType.FALL_DETECTED,
            confidence_score=0.88,
            processed=True,
            status=AlertStatus.OPEN.value,
        ),
        Alert(
            id=alert_other_property_id,
            camera_id=camera_two_id,
            incident_id=incident_other_property_id,
            frame_timestamp=base_time - timedelta(minutes=3),
            detection_type=DetectionType.WEAPON_DETECTED,
            confidence_score=0.91,
            processed=True,
            status=AlertStatus.OPEN.value,
        ),
    ]

    async with SessionLocal() as db:
        db.add_all(
            [
                neighbourhood,
                property_one,
                property_two,
                camera_one,
                camera_two,
                viewer,
                officer,
                outsider,
                viewer_membership,
                officer_membership,
                viewer_property_membership,
                incident_weapon,
                incident_human,
                incident_fall,
                incident_other_property,
                *alerts,
            ]
        )

        await db.commit()

    scenario = {
        "neighbourhood_id": neighbourhood_id,
        "property_one_id": property_one_id,
        "property_two_id": property_two_id,
        "camera_one_id": camera_one_id,
        "camera_two_id": camera_two_id,
        "viewer": viewer,
        "officer": officer,
        "outsider": outsider,
        "incident_weapon_id": incident_weapon_id,
        "incident_human_id": incident_human_id,
        "incident_fall_id": incident_fall_id,
        "incident_other_property_id": incident_other_property_id,
        "base_time": base_time,
    }

    try:
        yield scenario
    finally:
        async with SessionLocal() as db:
            camera_ids = [
                camera_one_id,
                camera_two_id,
            ]

            incident_result = await db.execute(
                select(Alert.incident_id).where(
                    Alert.camera_id.in_(camera_ids)
                )
            )

            incident_ids = {
                incident_id
                for incident_id in incident_result.scalars().all()
                if incident_id is not None
            }

            await db.execute(
                delete(Alert).where(
                    Alert.camera_id.in_(camera_ids)
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
                    PropertyUser.user_id.in_(
                        [viewer_id, officer_id, outsider_id]
                    )
                )
            )

            await db.execute(
                delete(NeighbourhoodUser).where(
                    NeighbourhoodUser.user_id.in_(
                        [viewer_id, officer_id, outsider_id]
                    )
                )
            )

            await db.execute(
                delete(Camera).where(
                    Camera.id.in_(camera_ids)
                )
            )

            await db.execute(
                delete(Property).where(
                    Property.id.in_(
                        [property_one_id, property_two_id]
                    )
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_(
                        [viewer_id, officer_id, outsider_id]
                    )
                )
            )

            await db.execute(
                delete(Neighbourhood).where(
                    Neighbourhood.id == neighbourhood_id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_list_incidents_returns_one_summary_per_incident(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == 200
    assert body["pagination"]["total"] == 3
    assert len(body["data"]) == 3

    incident_ids = [item["id"] for item in body["data"]]

    assert len(incident_ids) == len(set(incident_ids))
    assert str(scenario["incident_weapon_id"]) in incident_ids
    assert str(scenario["incident_fall_id"]) in incident_ids
    assert str(scenario["incident_other_property_id"]) in incident_ids

    weapon_summary = next(
        item
        for item in body["data"]
        if item["id"] == str(scenario["incident_weapon_id"])
    )

    assert weapon_summary["alert_count"] == 2
    assert weapon_summary["representative_alert_id"] == (
        str(uuid.UUID(str(weapon_summary["representative_alert_id"])))
    )


@pytest.mark.asyncio
async def test_get_incident_returns_detail_with_all_alerts(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/{scenario['incident_weapon_id']}",
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == 200
    assert body["data"]["id"] == str(scenario["incident_weapon_id"])
    assert body["data"]["detection_type"] == "WEAPON_DETECTED"
    assert body["data"]["alert_count"] == 2
    assert len(body["data"]["alerts"]) == 2


@pytest.mark.asyncio
async def test_non_member_cannot_list_incidents(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        headers=make_headers(
            scenario["outsider"],
            NeighbourhoodRole.RESIDENT,
        ),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_member_cannot_get_incident_detail(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/{scenario['incident_weapon_id']}",
        headers=make_headers(
            scenario["outsider"],
            NeighbourhoodRole.RESIDENT,
        ),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_resident_sees_only_incidents_from_their_property(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        headers=make_headers(
            scenario["viewer"],
            NeighbourhoodRole.RESIDENT,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    incident_ids = {item["id"] for item in body["data"]}

    assert str(scenario["incident_weapon_id"]) in incident_ids
    assert str(scenario["incident_human_id"]) in incident_ids
    assert str(scenario["incident_fall_id"]) in incident_ids
    assert str(scenario["incident_other_property_id"]) not in incident_ids


@pytest.mark.asyncio
async def test_security_officer_sees_only_weapon_and_fall_incidents(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    incident_ids = {item["id"] for item in body["data"]}

    assert str(scenario["incident_weapon_id"]) in incident_ids
    assert str(scenario["incident_fall_id"]) in incident_ids
    assert str(scenario["incident_other_property_id"]) in incident_ids
    assert str(scenario["incident_human_id"]) not in incident_ids


@pytest.mark.asyncio
async def test_status_filter_returns_matching_incident(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        params={"status": "ACKNOWLEDGED"},
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    incident_ids = {item["id"] for item in body["data"]}

    assert incident_ids == {
        str(scenario["incident_weapon_id"])
    }


@pytest.mark.asyncio
async def test_camera_filter_returns_matching_incidents(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        params={
            "camera_id": str(scenario["camera_one_id"]),
        },
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    incident_ids = {item["id"] for item in body["data"]}

    assert str(scenario["incident_weapon_id"]) in incident_ids
    assert str(scenario["incident_fall_id"]) in incident_ids
    assert str(scenario["incident_other_property_id"]) not in incident_ids


@pytest.mark.asyncio
async def test_date_filter_excludes_old_incidents(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario
    base_time = scenario["base_time"]

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        params={
            "start_date": (
                base_time - timedelta(days=1)
            ).isoformat(),
            "end_date": (
                base_time + timedelta(minutes=1)
            ).isoformat(),
        },
        headers=make_headers(
            scenario["viewer"],
            NeighbourhoodRole.RESIDENT,
        ),
    )

    assert response.status_code == 200

    body = response.json()
    incident_ids = {item["id"] for item in body["data"]}

    assert str(scenario["incident_human_id"]) not in incident_ids
    assert str(scenario["incident_weapon_id"]) in incident_ids
    assert str(scenario["incident_fall_id"]) in incident_ids


@pytest.mark.asyncio
async def test_pagination_is_applied(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        params={
            "limit": 1,
            "offset": 1,
        },
        headers=make_headers(
            scenario["viewer"],
            NeighbourhoodRole.RESIDENT,
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["pagination"]["total"] == 3
    assert body["pagination"]["limit"] == 1
    assert body["pagination"]["offset"] == 1
    assert body["pagination"]["has_more"] is True
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_invalid_pagination_is_rejected(
    async_client: AsyncClient,
    incident_scenario,
):
    scenario = incident_scenario

    response = await async_client.get(
        f"/incidents/neighbourhoods/{scenario['neighbourhood_id']}",
        params={"limit": 0},
        headers=make_headers(
            scenario["officer"],
            NeighbourhoodRole.SECURITY_OFFICER,
        ),
    )

    assert response.status_code == 422
