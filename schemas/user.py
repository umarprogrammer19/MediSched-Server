from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, constr
from enum import Enum
from bson import ObjectId
from typing import List, Optional

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class TimeSlot(BaseModel):
    day: str
    start_time: str
    end_time: str
    is_booked: bool

class DoctorDetailsResponse(BaseModel):
    user: Optional[str] = None  # Use string for user ID to avoid nested UserResponse
    father_name: str
    gender: str
    country: str
    city: str
    qualification: str
    experience: int
    price_per_appointment: float
    available_time_slots: List[TimeSlot]
    description: str
    profile_picture_url: str

    model_config = ConfigDict(from_attributes=True)

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
    doctor_details: Optional[DoctorDetailsResponse] = None

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = ConfigDict(from_attributes=True)