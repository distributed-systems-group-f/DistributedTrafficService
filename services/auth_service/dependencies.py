from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db
from shared.auth import get_current_user


async def get_db_session(db: AsyncSession = Depends(get_db)):
    return db
