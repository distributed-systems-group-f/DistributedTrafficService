from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine(database_url: str | None = None):
    settings = get_settings()
    url = database_url or settings.database_url
    return create_async_engine(url, echo=False, pool_pre_ping=True)


def get_session_factory(engine=None):
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


_engine = None
_session_factory = None


def init_db():
    global _engine, _session_factory
    _engine = get_engine()
    _session_factory = get_session_factory(_engine)


async def get_db():
    global _session_factory
    if _session_factory is None:
        init_db()
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
