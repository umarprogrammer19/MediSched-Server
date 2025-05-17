from beanie import Link, Document
from datetime import datetime
from enum import Enum
from models.user import User
from models.doctor_details import TimeSlot


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELED = "canceled"


class Appointment(Document):
    patient: Link[User]
    doctor: Link[User]
    time_slot: TimeSlot
    status: AppointmentStatus = AppointmentStatus.PENDING
    payment_status: str  # "paid", "pending", "live"
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "appointments"
