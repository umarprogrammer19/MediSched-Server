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
