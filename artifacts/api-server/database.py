import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_raw_url = os.environ.get("SUPABASE_DATABASE_URL", "")

engine = None
AsyncSessionLocal = None

if _raw_url and (_raw_url.startswith("postgres://") or _raw_url.startswith("postgresql://")):
    _db_url = _raw_url
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    try:
        engine = create_async_engine(_db_url, echo=False)
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as e:
        print(f"[DB] Warning: Could not create engine: {e}")
        engine = None
        AsyncSessionLocal = None
elif _raw_url:
    print(f"[DB] Warning: SUPABASE_DATABASE_URL has invalid format. Must start with postgres:// or postgresql://")


class Base(DeclarativeBase):
    pass


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("SUPABASE_DATABASE_URL is not configured or has invalid format")
    async with AsyncSessionLocal() as session:
        yield session
