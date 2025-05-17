from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.doctor_details import (
    DoctorDetails,
) 
from models.appointment import Appointment
from models.message import Message
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["medisched_db"]


async def connect_to_mongo():
    await init_beanie(
        database=db, document_models=[User, DoctorDetails, Appointment, Message]
    )
    print("Successfully Connected to MongoDB")
