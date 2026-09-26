from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

# API engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10
)

#  Worker engine
worker_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
WorkerSessionLocal = async_sessionmaker(
    worker_engine, 
    class_=AsyncSession, 
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

DbSession = Annotated[AsyncSession, Depends(get_db)]

@asynccontextmanager
async def worker_session() -> AsyncGenerator[AsyncGenerator, None]:
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    session_local = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        async with session_local() as db:
            yield db
    finally:
        await engine.dispose()