#!/usr/bin/env python3
"""Database seeder script for development"""

import sys
import random
from uuid import uuid4, UUID
from datetime import datetime, timedelta
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
from app.models.detection_event import DetectionEvent, DetectionType
from app.models.alert import Alert, AlertStatus

# Fixed UUIDs for testing
NEIGHBOURHOOD_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("20000000-0000-0000-0000-000000000001")
PROPERTY_ID = UUID("30000000-0000-0000-0000-000000000001")
CAMERA_ID = UUID("40000000-0000-0000-0000-000000000001")
ZONE_ID = UUID("50000000-0000-0000-0000-000000000001")

def seed_database():
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
            cognito_sub="00000000-0000-0000-0000-000000000001",
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
        test_camera = Camera(
            id=CAMERA_ID,
            property_id=PROPERTY_ID,
            neighbourhood_id=NEIGHBOURHOOD_ID,
            visibility=CameraVisibilityEnum.PRIVATE,
            location="Front Entrance",
            rtsp_url="rtsp://camera.local:554/stream"
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

                detection_event = DetectionEvent(
                    id=uuid4(),
                    camera_id=CAMERA_ID,
                    frame_timestamp=event_time,
                    detection_type=random.choice(detection_types),
                    confidence_score=round(random.uniform(0.55, 0.99), 2),
                    thumbnail_url=None,
                    processed=True,
                )

                db.add(detection_event)
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
                    detection_event_id=detection_event.id,
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

        #commit all changes
        db.commit()
        print("\nDatabase seeded successfully!")
        print("\nTest Credentials:")
        print("Email: testuser@example.com")
        print("Cognito Sub: 00000000-0000-0000-0000-000000000001")
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
    seed_database()
