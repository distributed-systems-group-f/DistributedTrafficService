from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine(database_url: str | None = None):
    global _engine
    if database_url is None and _engine is not None:
        return _engine

    settings = get_settings()
    url = database_url or settings.database_url
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    if database_url is None:
        _engine = engine
    return engine


def get_session_factory(engine=None):
    global _session_factory
    if engine is None:
        if _session_factory is not None:
            return _session_factory
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return _session_factory

    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
