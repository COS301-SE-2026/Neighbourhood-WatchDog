import asyncio
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from uuid import UUID

from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.alert import Alert, AlertStatus, DetectionType
from app.models.audit_log import AuditAction, AuditLog, TargetEntity
from app.models.camera import Camera, CameraVisibilityEnum
from app.models.camera_detection_zone import CameraDetectionZone
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_join_request import JoinRequestStatus, NeighbourhoodJoinRequest
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.pairing_token import PairingToken
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.retention_policy import RetentionPolicy
from app.models.risk_score_history import RiskLevel, RiskScoreHistory
from app.models.risk_threshold_config import RiskThresholdConfig
from app.models.user import User, UserRole
from app.models.zone import GeospatialZone, SensitivityLevel
from app.services.rtsp_encryption import encrypt_rtsp_url


NEIGHBOURHOOD_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("20000000-0000-0000-0000-000000000001")
PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000001")
CAMERA_ID = UUID("40000000-0000-0000-0000-000000000001")
ZONE_ID = UUID("50000000-0000-0000-0000-000000000001")
AUDIT_LOG_ID = UUID("60000000-0000-0000-0000-000000000001")
EDGE_AGENT_CREDENTIAL_ID = UUID("70000000-0000-0000-0000-000000000001")
TEST_ALERT_ID = UUID("80000000-0000-0000-0000-000000000001")

SECOND_USER_ID = UUID("20000000-0000-0000-0000-000000000002")
OFFICER_USER_ID = UUID("20000000-0000-0000-0000-000000000003")
SECOND_PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000002")
OFFICER_PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000003")
CAMERA_TWO_ID = UUID("40000000-0000-0000-0000-000000000002")
CAMERA_THREE_ID = UUID("40000000-0000-0000-0000-000000000003")
CAMERA_ZONE_ID = UUID("d0000000-0000-0000-0000-000000000001")
JOIN_REQUEST_ID = UUID("90000000-0000-0000-0000-000000000001")
APPROVED_REQUEST_ID = UUID("90000000-0000-0000-0000-000000000002")
REJECTED_REQUEST_ID = UUID("90000000-0000-0000-0000-000000000003")

FOURTH_USER_ID = UUID("20000000-0000-0000-0000-000000000004")
FOURTH_PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000004")
DENY_TEST_REQUEST_ID = UUID("90000000-0000-0000-0000-000000000004")
RISK_HISTORY_IDS = [
	UUID("a0000000-0000-0000-0000-000000000001"),
	UUID("a0000000-0000-0000-0000-000000000002"),
	UUID("a0000000-0000-0000-0000-000000000003"),
]
NOTIFICATION_IDS = [
	UUID("b0000000-0000-0000-0000-000000000001"),
	UUID("b0000000-0000-0000-0000-000000000002"),
]
PAIRING_TOKEN_ID = UUID("c0000000-0000-0000-0000-000000000001")
RETENTION_POLICY_IDS = [
	UUID("e0000000-0000-0000-0000-000000000001"),
	UUID("e0000000-0000-0000-0000-000000000002"),
	UUID("e0000000-0000-0000-0000-000000000003"),
]

PRIMARY_COGNITO_SUB = "a16cd2b8-c0c1-70f7-1fb6-17b5cea57bcf"
JOIN_CODE = "E2E_TEST_CODE_001"
PAIRING_TOKEN = "e2e-pairing-token-001"
DEV_AGENT_TOKEN = "dev-token"
NOW = datetime.now(timezone.utc)


def _user(user_id: UUID, email: str, first_name: str, last_name: str, cognito_sub: str, role: UserRole = UserRole.RESIDENT) -> User:
	return User(
		id=user_id,
		email=email,
		first_name=first_name,
		last_name=last_name,
		cognito_sub=cognito_sub,
		system_role=role,
	)


def _camera(camera_id: UUID, property_id: UUID, name: str, location: str, visibility: CameraVisibilityEnum) -> Camera:
	return Camera(
		id=camera_id,
		property_id=property_id,
		name=name,
		visibility=visibility,
		location=location,
		rtsp_url=encrypt_rtsp_url(f"rtsp://e2e-camera.local:554/{camera_id}"),
		confidence_threshold=0.5,
		enabled=True,
	)


def _alert(
	alert_id: UUID,
	camera_id: UUID,
	detection_type: DetectionType,
	status: AlertStatus,
	timestamp: datetime,
	confidence: float,
	resolved_by: UUID | None = None,
) -> Alert:
	resolved_at = timestamp + timedelta(minutes=12) if status == AlertStatus.RESOLVED else None
	return Alert(
		id=alert_id,
		camera_id=camera_id,
		frame_timestamp=timestamp,
		detection_type=detection_type,
		confidence_score=confidence,
		processed=True,
		status=status.value,
		resolved_by=resolved_by,
		resolved_at=resolved_at,
		created_at=timestamp,
	)


async def seed_test_database() -> None:
	async with SessionLocal() as db:
		existing = await db.scalar(select(Neighbourhood.id).where(Neighbourhood.id == NEIGHBOURHOOD_ID))
		if existing is not None:
			print("E2E test data already exists")
			return

		neighbourhood = Neighbourhood(
			id=NEIGHBOURHOOD_ID,
			name="E2E Test Neighbourhood",
			location="Pretoria, Gauteng",
			join_code=JOIN_CODE,
		)
		primary_user = _user(USER_ID, "testuser@example.com", "Test", "User", PRIMARY_COGNITO_SUB)
		resident_user = _user(SECOND_USER_ID, "e2e.resident@example.com", "E2E", "Resident", "e2e-resident-cognito-sub")
		officer_user = _user(
			OFFICER_USER_ID,
			"e2e.officer@example.com",
			"E2E",
			"Officer",
			"e2e-officer-cognito-sub",
			UserRole.SECURITY_OFFICER,
		)
		deny_flow_user = _user(
			FOURTH_USER_ID,
			"e2e.deny-flow@example.com",
			"E2E",
			"DenyFlow",
			"e2e-deny-flow-cognito-sub",
		)
		db.add_all([neighbourhood, primary_user, resident_user, officer_user, deny_flow_user])
		await db.flush()

		db.add_all(
			[
				Property(
					id=PROPERTY_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					address="123 Test Street\nPretoria\nGauteng\n0001",
					property_type=PropertyTypeEnum.PRIVATE,
				),
				Property(
					id=SECOND_PROPERTY_ID,
					neighbourhood_id=None,
					address="45 Join Request Road\nPretoria\nGauteng\n0002",
					property_type=PropertyTypeEnum.PRIVATE,
				),
				Property(
					id=OFFICER_PROPERTY_ID,
					neighbourhood_id=None,
					address="67 Review Avenue\nPretoria\nGauteng\n0003",
					property_type=PropertyTypeEnum.PUBLIC,
				),
				Property(
					id=FOURTH_PROPERTY_ID,
					neighbourhood_id=None,
					address="89 Deny Flow Close\nPretoria\nGauteng\n0004",
					property_type=PropertyTypeEnum.PRIVATE,
				),
				PropertyUser(user_id=USER_ID, property_id=PROPERTY_ID, is_admin=True),
				PropertyUser(user_id=SECOND_USER_ID, property_id=SECOND_PROPERTY_ID, is_admin=True),
				PropertyUser(user_id=OFFICER_USER_ID, property_id=OFFICER_PROPERTY_ID, is_admin=True),
				PropertyUser(user_id=FOURTH_USER_ID, property_id=FOURTH_PROPERTY_ID, is_admin=True),
				NeighbourhoodUser(
					user_id=USER_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					role=NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
				),
				NeighbourhoodUser(
					user_id=OFFICER_USER_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					role=NeighbourhoodRole.SECURITY_OFFICER,
				),
			]
		)
		await db.flush()

		db.add_all(
			[
				_camera(CAMERA_ID, PROPERTY_ID, "Front Entrance", "Front Entrance", CameraVisibilityEnum.PUBLIC),
				_camera(CAMERA_TWO_ID, PROPERTY_ID, "Back Gate", "Back Gate", CameraVisibilityEnum.RESTRICTED),
				_camera(CAMERA_THREE_ID, PROPERTY_ID, "Garage", "Garage", CameraVisibilityEnum.PRIVATE),
				*[
					RetentionPolicy(
						id=policy_id,
						camera_id=camera_id,
						hot_seconds=86400,
						warm_seconds=604800,
						cold_seconds=2592000,
					)
					for policy_id, camera_id in zip(RETENTION_POLICY_IDS, [CAMERA_ID, CAMERA_TWO_ID, CAMERA_THREE_ID])
				],
				CameraDetectionZone(
					id=CAMERA_ZONE_ID,
					camera_id=CAMERA_ID,
					name="Front Gate Detection Area",
					polygon=[[0.1, 0.1], [0.9, 0.1], [0.9, 0.85], [0.1, 0.85]],
				),
				GeospatialZone(
					id=ZONE_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					name="Main Security Zone",
					polygon_boundary=WKTElement(
						"POLYGON((28.0 -25.0, 28.1 -25.0, 28.1 -25.1, 28.0 -25.1, 28.0 -25.0))",
						srid=4326,
					),
					sensitivity_level=SensitivityLevel.HIGH,
				),
			]
		)
		await db.flush()

		alert_rows = [
			_alert(TEST_ALERT_ID, CAMERA_ID, DetectionType.WEAPON_DETECTED, AlertStatus.OPEN, NOW - timedelta(minutes=5), 0.96),
			_alert(UUID("80000000-0000-0000-0000-000000000002"), CAMERA_ID, DetectionType.LOITERING, AlertStatus.ACKNOWLEDGED, NOW - timedelta(hours=2), 0.88),
			_alert(UUID("80000000-0000-0000-0000-000000000003"), CAMERA_TWO_ID, DetectionType.PERIMETER_SCAN, AlertStatus.RESOLVED, NOW - timedelta(days=1), 0.79, USER_ID),
			_alert(UUID("80000000-0000-0000-0000-000000000004"), CAMERA_TWO_ID, DetectionType.HUMAN_PRESENCE, AlertStatus.OPEN, NOW - timedelta(days=8), 0.91),
			_alert(UUID("80000000-0000-0000-0000-000000000005"), CAMERA_THREE_ID, DetectionType.FALL_DETECTED, AlertStatus.RESOLVED, NOW - timedelta(days=30), 0.73, USER_ID),
			_alert(UUID("80000000-0000-0000-0000-000000000006"), CAMERA_ID, DetectionType.HUMAN_PRESENCE, AlertStatus.OPEN, NOW - timedelta(days=120), 0.62),
		]
		db.add_all(alert_rows)
		await db.flush()

		db.add_all(
			[
				Notification(
					id=NOTIFICATION_IDS[0],
					alert_id=TEST_ALERT_ID,
					user_id=USER_ID,
					channel=NotificationChannel.EMAIL,
					status=NotificationStatus.SENT,
					sent_at=NOW - timedelta(minutes=4),
				),
				Notification(
					id=NOTIFICATION_IDS[1],
					alert_id=alert_rows[1].id,
					user_id=USER_ID,
					channel=NotificationChannel.WHATSAPP,
					status=NotificationStatus.FAILED,
					error_message="E2E simulated delivery failure",
					sent_at=NOW - timedelta(hours=2),
				),
				RiskThresholdConfig(
					id=UUID("a1000000-0000-0000-0000-000000000001"),
					neighbourhood_id=None,
					low_max=30.0,
					medium_max=70.0,
				),
				RiskThresholdConfig(
					id=UUID("a1000000-0000-0000-0000-000000000002"),
					neighbourhood_id=NEIGHBOURHOOD_ID,
					low_max=25.0,
					medium_max=65.0,
				),
				*[
					RiskScoreHistory(
						id=history_id,
						neighbourhood_id=NEIGHBOURHOOD_ID,
						score=score,
						classification=classification,
						alert_count=alert_count,
						calculated_at=NOW - timedelta(days=days_ago),
					)
					for history_id, score, classification, alert_count, days_ago in [
						(RISK_HISTORY_IDS[0], 18.0, RiskLevel.LOW, 2, 30),
						(RISK_HISTORY_IDS[1], 48.0, RiskLevel.MEDIUM, 7, 14),
						(RISK_HISTORY_IDS[2], 82.0, RiskLevel.HIGH, 14, 1),
					]
				],
				PairingToken(
					id=PAIRING_TOKEN_ID,
					token=PAIRING_TOKEN,
					property_id=PROPERTY_ID,
					created_at=NOW - timedelta(minutes=1),
					expires_at=NOW + timedelta(minutes=9),
				),
				EdgeAgentCredential(
					id=EDGE_AGENT_CREDENTIAL_ID,
					property_id=PROPERTY_ID,
					key_hash=hashlib.sha256(DEV_AGENT_TOKEN.encode()).hexdigest(),
					created_at=NOW,
				),
				NeighbourhoodJoinRequest(
					id=JOIN_REQUEST_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					property_id=SECOND_PROPERTY_ID,
					user_id=SECOND_USER_ID,
					status=JoinRequestStatus.PENDING,
					created_at=NOW - timedelta(hours=3),
				),
				NeighbourhoodJoinRequest(
					id=APPROVED_REQUEST_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					property_id=PROPERTY_ID,
					user_id=USER_ID,
					status=JoinRequestStatus.APPROVED,
					created_at=NOW - timedelta(days=4),
					resolved_at=NOW - timedelta(days=3),
				),
				NeighbourhoodJoinRequest(
					id=REJECTED_REQUEST_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					property_id=OFFICER_PROPERTY_ID,
					user_id=OFFICER_USER_ID,
					status=JoinRequestStatus.REJECTED,
					created_at=NOW - timedelta(days=6),
					resolved_at=NOW - timedelta(days=5),
				),
				NeighbourhoodJoinRequest(
					id=DENY_TEST_REQUEST_ID,
					neighbourhood_id=NEIGHBOURHOOD_ID,
					property_id=FOURTH_PROPERTY_ID,
					user_id=FOURTH_USER_ID,
					status=JoinRequestStatus.PENDING,
					created_at=NOW - timedelta(hours=1),
				),
				AuditLog(
					id=AUDIT_LOG_ID,
					user_id=USER_ID,
					action=AuditAction.CREATE,
					target_entity_type=TargetEntity.CAMERA,
					target_entity_id=CAMERA_ID,
					old_values=None,
					new_values={"name": "Front Entrance", "visibility": "PUBLIC"},
					timestamp=NOW - timedelta(days=3),
				),
				AuditLog(
					user_id=USER_ID,
					action=AuditAction.UPDATE,
					target_entity_type=TargetEntity.ALERT,
					target_entity_id=alert_rows[1].id,
					old_values={"status": "OPEN"},
					new_values={"status": "ACKNOWLEDGED"},
					timestamp=NOW - timedelta(hours=2),
				),
				AuditLog(
					user_id=USER_ID,
					action=AuditAction.DELETE,
					target_entity_type=TargetEntity.CAMERADETECTIONZONE,
					target_entity_id=CAMERA_ZONE_ID,
					old_values={"name": "Old Zone"},
					new_values=None,
					timestamp=NOW - timedelta(days=1),
				),
			]
		)
		await db.commit()
		print("E2E test database seeded successfully")
		print(f"Primary Cognito sub: {PRIMARY_COGNITO_SUB}")
		print(f"Neighbourhood ID: {NEIGHBOURHOOD_ID}")
		print(f"Property ID: {PROPERTY_ID}")
		print(f"Pending join request ID: {JOIN_REQUEST_ID}")
		print(f"Pairing token: {PAIRING_TOKEN}")


if __name__ == "__main__":
	try:
		asyncio.run(seed_test_database())
	except Exception as exc:
		print(f"Error seeding E2E database: {exc}", file=sys.stderr)
		raise