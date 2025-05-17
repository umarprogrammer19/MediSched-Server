from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.user import User
from auth.auth_handler import get_current_user

router = APIRouter(prefix="/user")


class ProfileUpdate(BaseModel):
    full_name: Optional[str]
    phone_number: Optional[str]


@router.put("/profile")
async def update_profile(
    update_data: ProfileUpdate, current_user: str = Depends(get_current_user)
):
    user = await User.find_one(User.id == current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.full_name:
        user.full_name = update_data.full_name
    if update_data.phone_number:
        user.phone_number = update_data.phone_number

    await user.save()
    return {"msg": "Profile updated successfully"}
