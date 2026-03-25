from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "driver"
    plate_number: Optional[str] = None
    region: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class UserProfile(BaseModel):
    id: str
    email: str
    role: str
    plate_number: Optional[str] = None
    region: Optional[str] = None
