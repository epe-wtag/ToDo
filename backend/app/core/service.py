from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import generate_verification_token

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

app = FastAPI()

bearer_scheme = HTTPBearer()

templates = Jinja2Templates(directory="app/templates")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
TOKEN_EXPIRE_MINUTES = 30


def load_template(template_name: str, context: dict) -> str:
    template = templates.get_template(template_name)
    return template.render(context)


async def simple_send(email: EmailStr, token: str) -> JSONResponse:
    verify_url = "http://127.0.0.1:8000/api/v1/auth/verify"
    context = {"verify_url": verify_url, "email": email, "token": token}
    html = load_template("verification_email.html", context)

    message = MessageSchema(
        subject="Verification Mail",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "Email has been sent"})


async def send_verification_email(email: str) -> None:
    verification_token = generate_verification_token(email)
    await simple_send(email, verification_token)


async def send_reset_email(email: EmailStr, token: str) -> JSONResponse:
    context = {"email": email, "token": token}
    html = load_template("reset_password_email.html", context)

    message = MessageSchema(
        subject="Reset Password",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "Email has been sent"})
