from fastapi import FastAPI
from database import connect_to_mongo
from auth.routes import router as auth_router
from admin.routes import router as admin_router
from doctor.routes import router as doctor_router
from appointment.routes import router as appointment_router
from user.routes import router as user_router
from message.routes import router as message_router
from payment.routes import router as payment_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development); replace with specific origins in production, e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
async def startup():
    await connect_to_mongo()

# All Routes Endpoint Setup 
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(doctor_router, prefix="/api", tags=["doctor"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(appointment_router, prefix="/api", tags=["appointment"])
app.include_router(user_router, prefix="/api", tags=["user"])
app.include_router(message_router, prefix="/api", tags=["message"])
app.include_router(payment_router, prefix="/api", tags=["payment"])
