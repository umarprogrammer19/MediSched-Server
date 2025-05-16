from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()


async def connect_to_mongo():
    await init_beanie(database=db, document_models=[User])
    print("Connected to MongoDB")
