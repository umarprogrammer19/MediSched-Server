from pydantic import BaseModel, EmailStr, constr
from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: constr(min_length=11, max_length=15)  # type: ignore
    password: constr(min_length=8)  # type: ignore


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    is_verified: bool

    class Config:
        from_attributes = True
