#!/usr/bin/env python3
"""Recreate database schema from models"""

import asyncio

from sqlalchemy import text

from app.core.database import engine, Base
import app.models #noqa: F401

async def recreate_database():
    """Drop all tables and recreate from models"""
    print("Dropping all tables...")
    async with engine.begin() as connection:

        await connection.execute(text("DROP SCHEMA public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
        
    print("Tables dropped")

    print("Re-enabling PostGIS extension")
    async with engine.begin() as connection:
        
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    print("PostGIS enabled")

    print("Creating all tables from models...")
    async with engine.begin() as connection:
      
        await connection.run_sync(Base.metadata.create_all)

    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(recreate_database())
