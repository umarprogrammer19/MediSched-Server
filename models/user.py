from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(Document):
    email: EmailStr
    full_name: str
    hashed_password: str
    role: UserRole
    is_active: bool = True
    # Add doctor-specific fields here (if role == doctor)
    specialties: Optional[List[str]] = None
    available_slots: Optional[List[str]] = None  # e.g. ["2023-05-15T10:00"]

    class Settings:
        name = "users"  # MongoDB collection name

    def verify_password(self, plain_password: str, pwd_context) -> bool:
        return pwd_context.verify(plain_password, self.hashed_password)
