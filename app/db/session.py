from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


engine: Optional[AsyncEngine] = None
session_factory: Optional[sessionmaker[AsyncSession]] = None


def init_db() -> None:
    global engine, session_factory
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncSession:
    if session_factory is None:
        init_db()
    async with session_factory() as session:  # type: ignore[call-arg]
        yield session
