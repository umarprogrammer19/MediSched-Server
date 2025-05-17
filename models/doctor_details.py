from pydantic import BaseModel
from typing import List
from beanie import Document, Link
from models.user import User


class TimeSlot(BaseModel):
    day: str  # e.g., "Mon", "Tue", etc.
    start_time: str  # e.g., "09:00"
    end_time: str  # e.g., "09:30"
    is_booked: bool = False


class DoctorDetails(Document):
    user: Link[User]  # Reference to the User document
    father_name: str
    gender: str
    country: str
    city: str
    qualification: str
    experience: int  # in years
    price_per_appointment: float  # in USD
    available_time_slots: List[TimeSlot] = []  # List of available slots
    description: str
    profile_picture_url: str  # Cloudinary URL

    class Settings:
        name = "doctor_details"
