from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from auth.auth_handler import get_current_user
from models.user import User, UserRole
from models.doctor_details import DoctorDetails, TimeSlot
from utils.email_utils import send_doctor_application_email
import cloudinary.uploader
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from schemas.user import UserResponse
import json
from bson import ObjectId
from bson.errors import InvalidId

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

class ApplicationResponse(BaseModel):
    msg: str

@router.post("/apply", response_model=ApplicationResponse)
async def apply_for_doctor(
    application: str = Form(...),
    profile_picture: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    # Log the current_user ID for debugging
    print(f"Current user ID: {current_user}")

    # Convert current_user to ObjectId
    try:
        user_id = ObjectId(current_user)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format"
        )

    # Find the user
    user = await User.find_one(User.id == user_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check user role and pending request
    if user.role == UserRole.DOCTOR or user.doctor_request_pending:
        raise HTTPException(
            status_code=400,
            detail="Already a doctor or request pending"
        )

    # Parse the application JSON string
    application_data = json.loads(application)

    # Validate the application data with DoctorApplication
    application_obj = DoctorApplication(**application_data)

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
        father_name=application_obj.father_name,
        gender=application_obj.gender,
        country=application_obj.country,
        city=application_obj.city,
        qualification=application_obj.qualification,
        experience=application_obj.experience,
        price_per_appointment=application_obj.price_per_appointment,
        available_time_slots=application_obj.available_time_slots,
        description=application_obj.description,
        profile_picture_url=profile_picture_url,
    )
    await doctor_details.insert()

    # Update user
    user.doctor_details = doctor_details
    user.doctor_request_pending = True
    await user.save()

    # Notify admin
    send_doctor_application_email("uhhfj0345@gmail.com", user.email)

    return ApplicationResponse(msg="Application submitted successfully")

# Rest of the code remains the same
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

@router.get("/", response_model=List[UserResponse])
async def get_all_doctors():
    doctors = await User.find(User.role == UserRole.DOCTOR, fetch_links=True).to_list()
    if not doctors:
        raise HTTPException(status_code=404, detail="No doctors found")
    return [UserResponse.from_orm(doctor) for doctor in doctors]