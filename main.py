from fastapi import FastAPI
from database import connect_to_mongo
from auth.routes import router as auth_router

app = FastAPI()


@app.on_event("startup")
async def startup():
    await connect_to_mongo()


app.include_router(auth_router, prefix="/auth", tags=["auth"])
