from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid


class UserRole(str, Enum):
    DRIVER = "driver"
    ENFORCEMENT_AGENT = "enforcement_agent"
    ADMIN = "admin"


class BaseUser(BaseModel):
    id: str
    email: str
    role: UserRole
    region: Optional[str] = None


class Driver(BaseUser):
    plate_number: Optional[str] = None
    role: UserRole = UserRole.DRIVER


class EnforcementAgent(BaseUser):
    badge_number: Optional[str] = None
    role: UserRole = UserRole.ENFORCEMENT_AGENT


class Admin(BaseUser):
    role: UserRole = UserRole.ADMIN
