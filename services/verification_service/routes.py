from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db, init_db
from shared.auth import get_current_user
from schemas import VerificationResult
import service

router = APIRouter()

init_db()


@router.get("/{plate_number}", response_model=VerificationResult)
async def verify_plate(
    plate_number: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.verify_plate(db, plate_number.upper())
