from beanie import Document, Link
from models.user import User
from datetime import datetime

class Message(Document):
    sender: Link[User]
    receiver: Link[User]
    content: str
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "messages"
