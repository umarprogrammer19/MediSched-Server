from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY not set in environment variables")

router = APIRouter()

class PaymentSessionRequest(BaseModel):
    amount: int
    currency: str
    doctor_id: str
    doctor_name: str
    metadata: dict = None  

@router.post("/payment/create")
async def create_checkout_session(request: PaymentSessionRequest):
    logger.info(f"Creating checkout session with request: {request}")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": request.currency,
                    "product_data": {
                        "name": f"Appointment with {request.doctor_name}",
                    },
                    "unit_amount": request.amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"http://localhost:3000/appointment-success?doctorId={request.doctor_id}",
            cancel_url="http://localhost:3000/appointment-cancelled",
            metadata=request.metadata or {"doctor_id": request.doctor_id},
        )
        logger.info(f"Checkout session created successfully: {session.id}")
        return {"sessionId": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")