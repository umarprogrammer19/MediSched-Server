from beanie import Document, Link
from pydantic import Field
from typing import Optional
from enum import Enum
from datetime import datetime
from models.user import (
    User,
)


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    FAILED = "failed"


class Appointment(Document):
    patient: Link[User]  # Link to the patient User document
    doctor: Link[User]  # Link to the doctor User document
    appointment_datetime: datetime = Field(...)
    status: AppointmentStatus = AppointmentStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    notes: Optional[str] = (
        None  # Optional field for any notes or reason for appointment
    )

    class Settings:
        name = "appointments"  # MongoDB collection name

    async def confirm(self):
        self.status = AppointmentStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
        await self.save()

    async def cancel(self):
        self.status = AppointmentStatus.CANCELLED
        self.updated_at = datetime.utcnow()
        await self.save()

    async def complete(self):
        self.status = AppointmentStatus.COMPLETED
        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_paid(self):
        self.payment_status = PaymentStatus.PAID
        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_failed_payment(self):
        self.payment_status = PaymentStatus.FAILED
        self.updated_at = datetime.utcnow()
        await self.save()
