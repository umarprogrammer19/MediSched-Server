from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from auth.auth_handler import get_current_user
from models.user import User, UserRole
from models.doctor_details import DoctorDetails, TimeSlot
from utils.email_utils import send_doctor_application_email
import cloudinary.uploader
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any
from schemas.user import UserResponse
import json
from beanie.odm.fields import PydanticObjectId
from beanie import Link
from bson import ObjectId
from bson.errors import InvalidId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    current_user: User = Depends(get_current_user),  # Corrected type hint to User
):
    # Log the current_user for debugging
    logger.info(f"Current user: {current_user.id if current_user else 'None'}")

    # Validate current_user
    if not current_user or not current_user.id:
        raise HTTPException(status_code=401, detail="Invalid user authentication")

    # Convert current_user.id to ObjectId
    try:
        user_id = ObjectId(current_user.id)
    except InvalidId:
        logger.error(f"Invalid user ID format: {current_user.id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Find the user
    user = await User.find_one(User.id == user_id)
    if user is None:
        logger.error(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # Check user role and pending request
    if user.role == UserRole.DOCTOR or user.doctor_request_pending:
        logger.warning(f"User {user_id} already a doctor or has a pending request")
        raise HTTPException(status_code=400, detail="Already a doctor or request pending")

    # Parse the application JSON string
    try:
        application_data = json.loads(application)
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in application data")
        raise HTTPException(status_code=400, detail="Invalid application data format")

    # Validate the application data with DoctorApplication
    application_obj = DoctorApplication(**application_data)

    # Upload profile picture to Cloudinary
    try:
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        )
        upload_result = cloudinary.uploader.upload(profile_picture.file)
        profile_picture_url = upload_result["secure_url"]
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")

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
    try:
        send_doctor_application_email("uhhfj0345@gmail.com", user.email)
    except Exception as e:
        logger.error(f"Failed to send doctor application email: {str(e)}")
        # Log the error but don't fail the request
        pass

    logger.info(f"Doctor application submitted successfully for user: {user_id}")
    return ApplicationResponse(msg="Application submitted successfully")

def convert_special_types(data):
    """Recursively convert PydanticObjectId and Link to serializable types."""
    if isinstance(data, dict):
        return {k: convert_special_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_special_types(item) for item in data]
    elif isinstance(data, PydanticObjectId):
        return str(data)
    elif isinstance(data, Link):
        # If the Link is resolved, extract the ID; otherwise, return None
        return str(data.ref.id) if data.ref and hasattr(data.ref, "id") else None
    return data

@router.get("/{id}")
async def get_doctor_profile(id: str) -> Dict[str, Any]:
    # Validate and convert the ID to ObjectId
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid doctor ID format")

    # Query the user with the given ID and role
    user = await User.find_one(
        User.id == ObjectId(id),
        User.role == UserRole.DOCTOR,
        fetch_links=True
    )

    # Check if the user exists and has doctor_details
    if not user or not user.doctor_details:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Manually resolve and serialize the doctor_details
    doctor_details_data = user.doctor_details.dict(by_alias=True, exclude_unset=True) if user.doctor_details else {}
    
    # Convert all PydanticObjectId and Link instances to serializable types
    doctor_details_data = convert_special_types(doctor_details_data)

    return {
        "id": str(user.id),  # Convert top-level ID to string
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "doctor_details": doctor_details_data,
    }
    
@router.get("/", response_model=List[UserResponse])
async def get_all_doctors():
    doctors = await User.find(User.role == UserRole.DOCTOR, fetch_links=True).to_list()
    if not doctors:
        raise HTTPException(status_code=404, detail="No doctors found")
    return [
        UserResponse(
            **{
                **doctor.dict(),
                "id": str(doctor.id),
                "doctor_details": {
                    **(doctor.doctor_details.dict() if doctor.doctor_details else {}),
                    "user": str(doctor.doctor_details.user.id) if doctor.doctor_details and doctor.doctor_details.user else None
                } if doctor.doctor_details else None
            }
        )
        for doctor in doctors
    ]