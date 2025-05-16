from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserCreate, UserResponse
from models.user import User, UserRole
from auth.auth_handler import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    create_email_token,
    verify_email_token,
)
from utils.email_utils import send_verification_email
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth")

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET_KEY not set in environment variables")
ALGORITHM = "HS256"


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    existing_user = await User.find_one(User.email == user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = hash_password(user.password)
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_pwd,
        role=UserRole.PATIENT,
        is_verified=False,
        doctor_request_pending=False,
    )
    await new_user.insert()
    token = create_email_token({"sub": user.email})
    # token = create_email_token({"sub": str(new_user.id)})
    send_verification_email(user.email, token)  # Removed 'await' here
    return UserResponse(
        id=str(new_user.id),
        full_name=new_user.full_name,
        email=new_user.email,
        phone_number=new_user.phone_number,
        role=new_user.role,
        is_verified=new_user.is_verified,
    )


@router.get("/verify-email")
async def verify_email(token: str):
    payload = verify_email_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    email = payload.get("sub")
    print("Email from token:", email)
    user = await User.find_one(User.email == email)
    print("User found:", user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"msg": "Email already verified"}
    user.is_verified = True
    await user.save()
    return {"msg": "Email verified successfully"}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = await User.find_one(User.email == form_data.username)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    response = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(db_user.id),
            "full_name": db_user.full_name,
            "email": db_user.email,
            "role": db_user.role,
        },
    }
    return response


@router.post("/refresh")
async def refresh(refresh_token: str):
    user_id = await verify_refresh_token(refresh_token)
    new_access_token = create_access_token(data={"sub": user_id})
    return {"access_token": new_access_token}
