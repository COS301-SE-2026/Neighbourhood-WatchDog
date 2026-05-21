#!/usr/bin/env python3
"""Recreate database schema from models"""

from app.core.database import engine, Base
from app import models  

def recreate_database():
    """Drop all tables and recreate from models"""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Tables dropped")

    print("Creating all tables from models...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")

if __name__ == "__main__":
    recreate_database()
