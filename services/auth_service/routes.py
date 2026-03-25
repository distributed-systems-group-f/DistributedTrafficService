from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db
from shared.auth import get_current_user
from shared.exceptions import AuthenticationError, UserNotFoundError
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserProfile
import service

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await service.register_user(
            db,
            email=req.email,
            password=req.password,
            role=req.role,
            plate_number=req.plate_number,
            region=req.region,
        )
        token = (await service.authenticate_user(db, req.email, req.password))[1]
        return TokenResponse(access_token=token, user_id=user.id, role=user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, token = await service.authenticate_user(db, req.email, req.password)
        return TokenResponse(access_token=token, user_id=user.id, role=user.role)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/profile", response_model=UserProfile)
async def profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user = await service.get_user_by_id(db, current_user["sub"])
        return UserProfile(
            id=user.id,
            email=user.email,
            role=user.role,
            plate_number=user.plate_number,
            region=user.region,
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
