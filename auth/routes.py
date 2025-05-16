from fastapi import APIRouter, HTTPException, Depends
from schemas.user import UserCreate, UserLogin, UserResponse
from models.user import User, UserRole
from auth.auth_handler import hash_password, verify_password, AuthJWT
from utils.email_utils import send_verification_email
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta
from beanie import PydanticObjectId

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
EMAIL_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_email_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


def verify_email_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


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
    token = create_email_token(user.email)
    await send_verification_email(user.email, token)
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
    email = verify_email_token(token)
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    await user.save()
    return {"msg": "Email verified successfully"}


@router.post("/login")
async def login(user: UserLogin, Authorize: AuthJWT = Depends()):
    db_user = await User.find_one(User.email == user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = Authorize.create_access_token(subject=str(db_user.id))
    refresh_token = Authorize.create_refresh_token(subject=str(db_user.id))
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
async def refresh(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_refresh_token_required()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Refresh token missing or invalid")
    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}
