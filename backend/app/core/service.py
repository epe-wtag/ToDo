import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.core.security import generate_verification_token



load_dotenv()


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL"),
    MAIL_PASSWORD=os.getenv("PASS"),
    MAIL_FROM=os.getenv("EMAIL"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


app = FastAPI()


bearer_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
VERIFICATION_KEY = os.getenv("VERIFICATION_KEY")
RESET_PASSWORD_KEY = os.getenv("RESET_PASSWORD_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
TOKEN_EXPIRE_MINUTES = 30



async def simple_send(email: EmailStr, token: str) -> JSONResponse:
    verify_url = "http://127.0.0.1:8000/api/v1/auth/verify"
    button_html = f"""
    <form method="post" action="{verify_url}">
        <input type="hidden" name="email" value="{email}">
        <input type="hidden" name="v_token" value="{token}">
        <button type="submit" style="background-color: #008CBA; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Verify Email</button>
    </form>
    """

    html = f"""
    <h3>This Token will be valid for 30 minutes only.</h3> 
    <br>
    <p>Click to Verify: {button_html}</p>
    """

    message = MessageSchema(
        subject="Verification Mail",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})


async def send_verification_email(email: str) -> None:
    verification_token = generate_verification_token(email)
    await simple_send(email, verification_token)
