import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_raw_url = os.environ.get("SUPABASE_DATABASE_URL")

engine = None
AsyncSessionLocal = None

if _raw_url:
    _db_url = _raw_url
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(_db_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("SUPABASE_DATABASE_URL is not configured")
    async with AsyncSessionLocal() as session:
        yield session
