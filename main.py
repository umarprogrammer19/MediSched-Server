from fastapi import FastAPI
from database import connect_to_mongo, close_mongo_connection

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


# Include routers here, e.g.
# from app.routers import user, appointment
# app.include_router(user.router)
# app.include_router(appointment.router)
