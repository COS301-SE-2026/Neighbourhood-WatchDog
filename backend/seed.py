#!/usr/bin/env python3
"""Database seeder script for development"""

import sys
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property, PropertyTypeEnum
from app.models.property_user import PropertyUser
from app.models.camera import Camera, CameraVisibilityEnum
from app.models.zone import GeospatialZone, SensitivityLevel
from app.models.retention_policy import RetentionPolicy

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

        #commit all changes
        db.commit()
        print("\nDatabase seeded successfully!")
        print("\nTest Credentials:")
        print("Email: testuser@example.com")
        print("Cognito Sub: 00000000-0000-0000-0000-000000000001")
        print("Neighbourhood: Test Neighbourhood")
        print("Property Address: 123 Test Street")

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
