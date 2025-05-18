from beanie import Document, Link
from pydantic import EmailStr
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Document):
    full_name: str
    email: EmailStr
    phone_number: str
    hashed_password: str
    role: UserRole = UserRole.PATIENT
    is_verified: bool = False
    doctor_request_pending: bool = False
    doctor_details: Optional[Link["DoctorDetails"]] = None

    class Settings:
        name = "users"