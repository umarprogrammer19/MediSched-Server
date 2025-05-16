from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.models.appointment import Appointment

# Import all your models here

import asyncio


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=db.client.your_database_name,
        document_models=[User, Appointment],  # add all models here
    )
    print("Connected to MongoDB")


async def close_mongo_connection():
    db.client.close()
