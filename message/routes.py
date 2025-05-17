from fastapi import APIRouter, Depends, HTTPException
from models.message import Message
from models.user import User
from auth.auth_handler import get_current_user

router = APIRouter(prefix="/message")


@router.post("/send")
async def send_message(
    receiver_id: str, content: str, current_user: str = Depends(get_current_user)
):
    sender = await User.find_one(User.id == current_user)
    receiver = await User.find_one(User.id == receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    message = Message(sender=sender, receiver=receiver, content=content)
    await message.insert()
    return {"msg": "Message sent"}


@router.get("/{user_id}")
async def get_messages(user_id: str, current_user: str = Depends(get_current_user)):
    messages = (
        await Message.find(
            (Message.sender.id == current_user and Message.receiver.id == user_id)
            | (Message.sender.id == user_id and Message.receiver.id == current_user)
        )
        .sort(-Message.timestamp)
        .to_list()
    )
    return messages
