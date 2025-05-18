from beanie import Document, Link
from pydantic import BaseModel
from typing import List

class TimeSlot(BaseModel):
    day: str
    start_time: str
    end_time: str
    is_booked: bool = False

class DoctorDetails(Document):
    user: Link["User"]
    father_name: str
    gender: str
    country: str
    city: str
    qualification: str
    experience: int
    price_per_appointment: float
    available_time_slots: List[TimeSlot] = []
    description: str
    profile_picture_url: str

    class Settings:
        name = "doctor_details"