import uuid
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.auth import create_access_token
from shared.exceptions import AuthenticationError, UserNotFoundError
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def register_user(db: AsyncSession, email: str, password: str, role: str, **kwargs) -> User:
    hashed = pwd_context.hash(password.encode("utf-8")[:72].decode("utf-8", errors="ignore"))
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=hashed,
        role=role,
        **kwargs,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    if not user or not pwd_context.verify(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    token = create_access_token(subject=user.id, role=user.role, extra={"email": user.email})
    return user, token


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user