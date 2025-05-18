from fastapi import HTTPException, Depends,APIRouter
from models.user import User, UserRole
from auth.auth_handler import get_current_admin
from bson import ObjectId

router = APIRouter(prefix="/admin")
@router.put("/{id}/approve")
async def approve_doctor_application(id: str, current_admin: User = Depends(get_current_admin)):  # Type hint as User
    # Log the current_admin for debugging
    print(f"Current admin: {current_admin}")

    # Check if the current user is an admin
    if current_admin is None or current_admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Find the user by ID
    user = await User.find_one(User.id == ObjectId(id))
    if user is None:
        print(f"User with ID {id} not found in the database")
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user has a pending doctor application
    if not user.doctor_request_pending:
        raise HTTPException(status_code=400, detail="No pending doctor application for this user")

    # Approve the application
    user.role = UserRole.DOCTOR
    user.doctor_request_pending = False
    await user.save()

    return {"msg": "Doctor application approved successfully"}