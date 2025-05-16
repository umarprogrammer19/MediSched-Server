from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER="templates/email",  # optional for templates
)


async def send_verification_email(email: str, token: str):
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Please verify your email by clicking on this link: http://localhost:3000/verify-email?token={token}",
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
