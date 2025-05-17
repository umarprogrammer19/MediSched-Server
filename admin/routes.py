from fastapi import HTTPException, Depends
from doctor.routes import router
from models.user import User, UserRole
from auth.auth_handler import get_current_user

@router.put("/admin/{user_id}/approve")
async def approve_doctor(
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    admin = await User.find_one(User.id == current_user)
    if admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await User.find_one(User.id == user_id)
    if not user or not user.doctor_request_pending:
        raise HTTPException(status_code=404, detail="User not found or no pending request")

    user.role = UserRole.DOCTOR
    user.doctor_request_pending = False
    await user.save()

    return {"msg": "Doctor application approved"}