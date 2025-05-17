from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from auth.auth_handler import get_current_user
from models.user import User, UserRole
from models.doctor_details import DoctorDetails, TimeSlot
from utils.email_utils import send_doctor_application_email
import cloudinary.uploader
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv()

router = APIRouter(prefix="/doctor")


class DoctorApplication(BaseModel):
    father_name: str
    gender: str
    country: str
    city: str
    qualification: str
    experience: int
    price_per_appointment: float
    available_time_slots: List[TimeSlot]
    description: str


@router.post("/apply")
async def apply_for_doctor(
    application: DoctorApplication,
    profile_picture: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    user = await User.find_one(User.id == current_user)
    if user.role == UserRole.DOCTOR or user.doctor_request_pending:
        raise HTTPException(
            status_code=400, detail="Already a doctor or request pending"
        )

    # Upload profile picture to Cloudinary
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )
    upload_result = cloudinary.uploader.upload(profile_picture.file)
    profile_picture_url = upload_result["secure_url"]

    # Create DoctorDetails document
    doctor_details = DoctorDetails(
        user=user,
        father_name=application.father_name,
        gender=application.gender,
        country=application.country,
        city=application.city,
        qualification=application.qualification,
        experience=application.experience,
        price_per_appointment=application.price_per_appointment,
        available_time_slots=application.available_time_slots,
        description=application.description,
        profile_picture_url=profile_picture_url,
    )
    await doctor_details.insert()

    # Update user
    user.doctor_details = doctor_details
    user.doctor_request_pending = True
    await user.save()

    # Notify admin
    send_doctor_application_email("uhhfj0345@gmail.com", user.email)

    return {"msg": "Application submitted successfully"}


@router.get("/{id}")
async def get_doctor_profile(id: str):
    user = await User.find_one(
        User.id == id, User.role == UserRole.DOCTOR, fetch_links=True
    )
    if not user or not user.doctor_details:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "doctor_details": user.doctor_details.dict(),
    }
