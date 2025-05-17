import yagmail
import os
from dotenv import load_dotenv

load_dotenv()


def send_verification_email(email: str, token: str):
    verification_url = f"http://127.0.0.1:8000/api/auth/verify-email?token={token}"
    html_body = f"""
    <h1>Verify Your Email</h1>
    <p>Please click the link to verify your email: <a href="{verification_url}">{verification_url}</a></p>
    """
    yag = yagmail.SMTP(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
    yag.send(to=email, subject="Verify Your MediSched Account", contents=[html_body])


def send_doctor_application_email(admin_email: str, user_email: str):
    html_body = f"""
    <h1>New Doctor Application</h1>
    <p>A new doctor application has been submitted by: {user_email}</p>
    <p>Please review it in the admin panel.</p>
    """
    yag = yagmail.SMTP(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
    yag.send(to=admin_email, subject="New Doctor Application", contents=[html_body])


def send_appointment_update_email(email: str, subject: str, appointment):
    html_body = f"""
    <h1>{subject}</h1>
    <p>Appointment Details:</p>
    <p>Doctor: {appointment.doctor.full_name}</p>
    <p>Patient: {appointment.patient.full_name}</p>
    <p>Time: {appointment.time_slot.day}, {appointment.time_slot.start_time} - {appointment.time_slot.end_time}</p>
    <p>Status: {appointment.status}</p>
    """
    yag = yagmail.SMTP(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
    yag.send(to=email, subject=subject, contents=[html_body])
