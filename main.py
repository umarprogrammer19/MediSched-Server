from fastapi import FastAPI
from database import connect_to_mongo
from auth.routes import router as auth_router
from admin.routes import router as admin_router
from doctor.routes import router as doctor_router
from appointment.routes import router as appointment_router
from user.routes import router as user_router
from message.routes import router as message_router

app = FastAPI()


@app.on_event("startup")
async def startup():
    await connect_to_mongo()


app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(doctor_router, prefix="/api", tags=["doctor"])
app.include_router(admin_router, prefix="/api", tags=["doctor"])
app.include_router(appointment_router, prefix="/api", tags=["appointment"])
app.include_router(user_router, prefix="/api", tags=["user"])
app.include_router(message_router, prefix="/api", tags=["message"])
