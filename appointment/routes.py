from fastapi import APIRouter, Depends, HTTPException
from auth.auth_handler import get_current_user
from models.user import User, UserRole
from models.appointment import Appointment, AppointmentStatus, TimeSlot
import stripe
import os
from dotenv import load_dotenv
from utils.email_utils import send_appointment_update_email
from models.doctor_details import DoctorDetails
from bson import ObjectId
import logging

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/appointment")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/current", response_model=list[dict])
async def get_all_appointments_for_doctor(
    current_user: User = Depends(get_current_user),
):
    try:
        # Verify the user is a doctor
        if current_user.role != UserRole.DOCTOR:
            raise HTTPException(
                status_code=403, detail="Only doctors can view their appointments"
            )

        # Fetch appointments with linked documents (doctor and patient)
        appointments = await Appointment.find(
            Appointment.doctor.id
            == ObjectId(current_user.id),  
            fetch_links=True,  
        ).to_list()

        # Transform appointments for response
        appointment_list = []
        for appointment in appointments:
            appointment_dict = {
                "appointment_id": str(appointment.id),
                "doctor_id": str(appointment.doctor.id),
                "patient_id": str(appointment.patient.id),
                "patient_details": {
                    "full_name": appointment.patient.full_name,
                    "email": appointment.patient.email,
                    "phone_number": appointment.patient.phone_number,
                },
                "time_slot": (
                    appointment.time_slot.dict()
                    if hasattr(appointment.time_slot, "dict")
                    else appointment.time_slot
                ),
                "payment_status": appointment.payment_status,
                "status": appointment.status.value,
                "created_at": appointment.created_at,
            }
            appointment_list.append(appointment_dict)
        return appointment_list
    except HTTPException as http_exc:
        logger.error(f"HTTP error: {str(http_exc.detail)}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/book")
async def book_appointment(
    doctor_id: str,
    time_slot: TimeSlot,
    payment_method: str,  
    current_user: User = Depends(get_current_user),
):

    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor ID format")

    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=403, detail="Only patients can book appointments"
        )

    # Find the doctor
    doctor = await User.find_one(User.id == ObjectId(doctor_id), fetch_links=True)
    print(f"Doctor query result: {doctor}")
    if not doctor or doctor.role != UserRole.DOCTOR or not doctor.doctor_details:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_details = doctor.doctor_details
    available_slots = [
        slot
        for slot in doctor_details.available_time_slots
        if not slot.is_booked
        and slot.day == time_slot.day
        and slot.start_time == time_slot.start_time
    ]

    if not available_slots:
        raise HTTPException(status_code=400, detail="Time slot not available")

    # Create appointment
    appointment = Appointment(
        patient=current_user,
        doctor=doctor,
        time_slot=time_slot,
        status=AppointmentStatus.PENDING,
        payment_status="pending" if payment_method == "online" else "live",
    )
    await appointment.insert()

    if payment_method == "online":
        stripe.PaymentIntent.create(
            amount=int(doctor_details.price_per_appointment * 100),
            currency="usd",
            metadata={"appointment_id": str(appointment.id)},
        )
        appointment.payment_status = "pending"
        await appointment.save()

    # Mark slot as booked
    for slot in doctor_details.available_time_slots:
        if slot.day == time_slot.day and slot.start_time == time_slot.start_time:
            slot.is_booked = True
    await doctor_details.save()

    return {
        "msg": "Appointment booked successfully",
        "appointment_id": str(appointment.id),
    }


@router.delete("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str, current_user: User = Depends(get_current_user)
):
    appointment = await Appointment.find_one(
        Appointment.id == appointment_id, fetch_links=True
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = await User.find_one(User.id == current_user.id)
    if patient.role != UserRole.PATIENT or appointment.patient.id != patient.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this appointment"
        )

    if appointment.status not in [
        AppointmentStatus.PENDING,
        AppointmentStatus.CONFIRMED,
    ]:
        raise HTTPException(status_code=400, detail="Cannot cancel this appointment")

    appointment.status = AppointmentStatus.CANCELED
    await appointment.save()

    # Free up the doctor's time slot
    doctor_details = await DoctorDetails.find_one(
        DoctorDetails.user.id == appointment.doctor.id
    )
    for slot in doctor_details.available_time_slots:
        if (
            slot.day == appointment.time_slot.day
            and slot.start_time == appointment.time_slot.start_time
        ):
            slot.is_booked = False
    await doctor_details.save()

    send_appointment_update_email(
        appointment.patient.email, "Appointment Canceled", appointment
    )
    send_appointment_update_email(
        appointment.doctor.email, "Appointment Canceled by Patient", appointment
    )

    return {"msg": "Appointment canceled successfully"}


@router.put("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    new_time_slot: TimeSlot,
    current_user: User = Depends(get_current_user),
):
    appointment = await Appointment.find_one(
        Appointment.id == appointment_id, fetch_links=True
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = await User.find_one(User.id == current_user.id)
    if patient.role != UserRole.PATIENT or appointment.patient.id != patient.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to reschedule this appointment"
        )

    if appointment.status not in [
        AppointmentStatus.PENDING,
        AppointmentStatus.CONFIRMED,
    ]:
        raise HTTPException(
            status_code=400, detail="Cannot reschedule this appointment"
        )

    doctor_details = await DoctorDetails.find_one(
        DoctorDetails.user.id == appointment.doctor.id
    )
    available_slots = [
        slot
        for slot in doctor_details.available_time_slots
        if not slot.is_booked
        and slot.day == new_time_slot.day
        and slot.start_time == new_time_slot.start_time
    ]

    if not available_slots:
        raise HTTPException(status_code=400, detail="New time slot not available")

    # Free the old time slot
    for slot in doctor_details.available_time_slots:
        if (
            slot.day == appointment.time_slot.day
            and slot.start_time == appointment.time_slot.start_time
        ):
            slot.is_booked = False

    # Book the new time slot
    for slot in doctor_details.available_time_slots:
        if (
            slot.day == new_time_slot.day
            and slot.start_time == new_time_slot.start_time
        ):
            slot.is_booked = True

    appointment.time_slot = new_time_slot
    appointment.status = AppointmentStatus.PENDING  # Requires doctor confirmation again
    await appointment.save()
    await doctor_details.save()

    send_appointment_update_email(
        appointment.patient.email, "Appointment Rescheduled", appointment
    )
    send_appointment_update_email(
        appointment.doctor.email, "Appointment Rescheduled by Patient", appointment
    )

    return {"msg": "Appointment rescheduled successfully"}


@router.put("/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str, current_user: User = Depends(get_current_user)
):
    appointment = await Appointment.find_one(
        Appointment.id == appointment_id, fetch_links=True
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    doctor = await User.find_one(User.id == current_user.id)
    if doctor.role != UserRole.DOCTOR or appointment.doctor.id != doctor.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to confirm this appointment"
        )

    if appointment.status != AppointmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Appointment cannot be confirmed")

    appointment.status = AppointmentStatus.CONFIRMED
    await appointment.save()

    send_appointment_update_email(
        appointment.patient.email, "Appointment Confirmed", appointment
    )
    send_appointment_update_email(
        appointment.doctor.email, "You confirmed an appointment", appointment
    )

    return {"msg": "Appointment confirmed successfully"}


@router.put("/{appointment_id}/reject")
async def reject_appointment(
    appointment_id: str, current_user: User = Depends(get_current_user)
):
    appointment = await Appointment.find_one(
        Appointment.id == appointment_id, fetch_links=True
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    doctor = await User.find_one(User.id == current_user.id)
    if doctor.role != UserRole.DOCTOR or appointment.doctor.id != doctor.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to reject this appointment"
        )

    if appointment.status != AppointmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Appointment cannot be rejected")

    appointment.status = AppointmentStatus.REJECTED
    await appointment.save()

    # Free up the time slot
    doctor_details = await DoctorDetails.find_one(
        DoctorDetails.user.id == appointment.doctor.id
    )
    for slot in doctor_details.available_time_slots:
        if (
            slot.day == appointment.time_slot.day
            and slot.start_time == appointment.time_slot.start_time
        ):
            slot.is_booked = False
    await doctor_details.save()

    send_appointment_update_email(
        appointment.patient.email, "Appointment Rejected", appointment
    )
    send_appointment_update_email(
        appointment.doctor.email, "You rejected an appointment", appointment
    )

    return {"msg": "Appointment rejected successfully"}
