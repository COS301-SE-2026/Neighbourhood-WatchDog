#!/usr/bin/env python3
"""Database seeder script for development"""

import secrets
import sys
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.risk_threshold_config import RiskThresholdConfig
from app.models.user import User, UserRole
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.camera import Camera, CameraVisibilityEnum
from app.models.zone import GeospatialZone, SensitivityLevel
from app.models.retention_policy import RetentionPolicy
from app.models.alert import Alert, AlertStatus, DetectionType
from app.models.audit_log import AuditLog, AuditAction
from app.services.rtsp_encryption import encrypt_rtsp_url

# Fixed UUIDs for testing
NEIGHBOURHOOD_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("20000000-0000-0000-0000-000000000001")
PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000001")
CAMERA_ID = UUID("40000000-0000-0000-0000-000000000001")
ZONE_ID = UUID("50000000-0000-0000-0000-000000000001")
AUDIT_LOG_ID = UUID("60000000-0000-0000-0000-000000000001")

# Entity types + the real IDs we have on hand for each, so target_entity_id
# points at something that actually exists (in case there's ever an FK added).
ENTITY_IDS_BY_TYPE = {
    "CAMERA": [CAMERA_ID],
    "PROPERTY": [PROPERTY_ID],
    "ZONE": [ZONE_ID],
    "USER": [USER_ID],
    "NEIGHBOURHOOD": [NEIGHBOURHOOD_ID],
}
TARGET_ENTITY_TYPES = list(ENTITY_IDS_BY_TYPE.keys())

FRONT_ENTRANCE = "Front Entrance"
SAMPLE_LOCATIONS = [FRONT_ENTRANCE, "Back Gate", "Garage", "Side Yard", "Driveway"]
SAMPLE_VISIBILITIES = ["PRIVATE", "PUBLIC"]
SAMPLE_STATUSES = ["ACTIVE", "INACTIVE"]

def _fake_values_for_action(action: AuditAction):
    """Build plausible old/new value dicts depending on the action type."""
    action_name = getattr(action, "name", str(action)).upper()

    snapshot = {
        "location": secrets.choice(SAMPLE_LOCATIONS),
        "visibility": secrets.choice(SAMPLE_VISIBILITIES),
        "status": secrets.choice(SAMPLE_STATUSES),
    }

    if "CREATE" in action_name:
        return None, snapshot
    if "DELETE" in action_name:
        return snapshot, None
    if "UPDATE" in action_name:
        updated = {**snapshot, "visibility": secrets.choice(SAMPLE_VISIBILITIES)}
        return snapshot, updated
    # e.g. VIEW / LOGIN / other non-mutating actions -> no diff to show
    return None, None


def seed_bulk_audit_logs(db: Session, user_id: UUID, count: int = 500) -> int:
    """Generate `count` randomized audit log rows spread across the last 90 days,
    so pagination, filtering, and sorting can actually be exercised."""
    actions = list(AuditAction)
    now = datetime.now(timezone.utc)

    logs = []
    for _ in range(count):
        action = secrets.choice(actions)
        entity_type = secrets.choice(TARGET_ENTITY_TYPES)
        entity_id = secrets.choice(ENTITY_IDS_BY_TYPE[entity_type])
        timestamp = now - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        old_values, new_values = _fake_values_for_action(action)

        logs.append(
            AuditLog(
                id=uuid4(),
                user_id=user_id,
                action=action,
                target_entity_type=entity_type,
                target_entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                timestamp=timestamp,
            )
        )

    db.add_all(logs)
    db.flush()
    return len(logs)


def seed_database(bulk_audit_count: int = 500):
    """Seed the database with test data"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if test data already exists
        existing_neighbourhood = db.query(Neighbourhood).filter(
            Neighbourhood.id == NEIGHBOURHOOD_ID
        ).first()

        if existing_neighbourhood:
            print("Test data already exists")
            return

        #make the test neighbourhood
        test_neighbourhood = Neighbourhood(
            id=NEIGHBOURHOOD_ID,
            name="Test Neighbourhood",
            location="Test Location, City",
            join_code="TEST_CODE_001"
        )
        db.add(test_neighbourhood)
        db.flush()
        print("Created test neighbourhood")

        #make test user
        test_user = User(
            id=USER_ID,
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            cognito_sub="a16cd2b8-c0c1-70f7-1fb6-17b5cea57bcf",
            role=UserRole.RESIDENT,
            neighbourhood_id=NEIGHBOURHOOD_ID
        )
        db.add(test_user)
        db.flush()
        print("Created test user")

        #create test property
        test_property = Property(
            id=PROPERTY_ID,
            neighbourhood_id=None,
            address="123 Test Street\nTest City\nGauteng\n1234",
            property_type=PropertyTypeEnum.PRIVATE
        )
        db.add(test_property)
        db.flush()
        print("Created test property")

        #link the  user to the prop
        property_user = PropertyUser(
            user_id=USER_ID,
            property_id=PROPERTY_ID,
            is_admin=True
        )
        db.add(property_user)
        db.flush()
        print("Linked user to property")

        #create test camera
        plaintext_rtsp_url = "rtsp://camera.local:554/stream"
        ciphertext_rtsp_url = encrypt_rtsp_url(plaintext_rtsp_url)

        test_camera = Camera(
            id=CAMERA_ID,
            name="Camera x",
            property_id=PROPERTY_ID,
            neighbourhood_id=NEIGHBOURHOOD_ID,
            visibility=CameraVisibilityEnum.PRIVATE,
            enabled=True,
            location="Front Entrance",
            rtsp_url=ciphertext_rtsp_url
        )
        db.add(test_camera)
        db.flush()
        print("Created test camera")

        #create retention policy for camera
        retention_policy = RetentionPolicy(
            id=uuid4(),
            camera_id=CAMERA_ID,
            hot_seconds=86400,    # 1 day
            warm_seconds=604800,  # 7 days
            cold_seconds=2592000  # 30 days
        )
        db.add(retention_policy)
        db.flush()
        print("Created retention policy")

        #create test zone
        test_zone = GeospatialZone(
            id=ZONE_ID,
            neighbourhood_id=NEIGHBOURHOOD_ID,
            name="Test Zone",
            polygon_boundary="POLYGON((28.0 -25.0, 28.1 -25.0, 28.1 -25.1, 28.0 -25.1, 28.0 -25.0))",
            sensitivity_level=SensitivityLevel.MEDIUM
        )
        db.add(test_zone)
        db.flush()
        print("Created test zone")

        #global default risk threshold config
        existing_default_threshold = db.query(RiskThresholdConfig).filter(
            RiskThresholdConfig.neighbourhood_id.is_(None)
        ).first()

        if not existing_default_threshold:
            default_threshold = RiskThresholdConfig(
                id=uuid4(),
                neighbourhood_id=None,
                low_max=30.0,
                medium_max=70.0 
            )
            db.add(default_threshold)
            db.flush()
            print("Created global risk threshold config")
        else:
            print("Global default risk threshold config already exists")

        alerts_created = 0
        detection_events_created = 0

        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        num_days = (today - one_year_ago).days

        detection_types = list(DetectionType)
        alert_statuses = [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]
        status_weights = [0.3, 0.2, 0.5]

        for day_offset in range(num_days):
            day = one_year_ago + timedelta(days=day_offset)

            recency_weight = day_offset / num_days
            daily_count = random.randint(0, int(2 + recency_weight * 8))

            for _ in range(daily_count):
                event_time = day + timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )

                alert = Alert(
                    id=uuid4(),
                    camera_id=CAMERA_ID,
                    frame_timestamp=event_time,
                    detection_type=random.choice(detection_types),
                    confidence_score=round(random.uniform(0.55, 0.99), 2),
                    thumbnail_url=None,
                    processed=True,
                    status=AlertStatus.OPEN.value,
                    created_at=event_time
                )

                db.add(alert)
                db.flush()  # need detection_event.id for the FK below
                detection_events_created += 1
 
                status = random.choices(alert_statuses, weights=status_weights)[0]
 
                resolved_by = None
                resolved_at = None
                if status == AlertStatus.RESOLVED:
                    resolved_by = USER_ID
                    resolved_at = event_time + timedelta(minutes=random.randint(5, 300))

                alert = Alert(
                    id=uuid4(),
                    camera_id=CAMERA_ID,
                    frame_timestamp=event_time,
                    detection_type=random.choice(detection_types),
                    confidence_score=round(random.uniform(0.55, 0.99), 2),
                    thumbnail_url=None,
                    processed=True,
                    status=status.value,
                    resolved_by=resolved_by,
                    resolved_at=resolved_at,
                    created_at=event_time,
                )
                db.add(alert)
                alerts_created += 1

            if day_offset % 30 == 0:
                db.flush()

        db.flush()
        print(f"Created {detection_events_created} test detection events")
        print(f"Created {alerts_created} test alerts spread across the last year")
        audit_create = AuditLog(
            id=AUDIT_LOG_ID,
            user_id=USER_ID,
            action=AuditAction.CREATE,
            target_entity_type="CAMERA",
            target_entity_id=CAMERA_ID,
            old_values=None,
            new_values={
                "location": FRONT_ENTRANCE,
                "visibility": "PRIVATE",
                "rtsp_url": ciphertext_rtsp_url,
            },
        )
        db.add(audit_create)

        audit_update = AuditLog(
            id=uuid4(),
            user_id=USER_ID,
            action=AuditAction.UPDATE,
            target_entity_type="CAMERA",
            target_entity_id=CAMERA_ID,
            old_values={"visibility": "PRIVATE"},
            new_values={"visibility": "PUBLIC"}
        )
        db.add(audit_update)

        db.flush()
        print("Created test audit logs")

        # Bulk audit logs for pagination/filtering/sorting testing
        print(f"Creating {bulk_audit_count} bulk audit log records...")
        created = seed_bulk_audit_logs(db, USER_ID, count=bulk_audit_count)
        print(f"Created {created} bulk audit log records")

        #commit all changes
        db.commit()
        print("\nDatabase seeded successfully!")
        print("\nTest Credentials:")
        print("Email: testuser@example.com")
        print("Cognito Sub: a16cd2b8-c0c1-70f7-1fb6-17b5cea57bcf")
        print("Neighbourhood: Test Neighbourhood")
        print("Property Address: 123 Test Street")
        print(f"Alerts seeded: {alerts_created}")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    # Optional: override the number of bulk audit logs, e.g. `python seed.py 2000`
    bulk_count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seed_database(bulk_audit_count=bulk_count)
