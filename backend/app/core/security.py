import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt
from pydantic import EmailStr
from starlette.responses import JSONResponse

from app.schema.auth_schema import TokenData

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
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, secret_key: str = SECRET_KEY) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def generate_verification_token(email: str) -> str:
    expiration_time = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"email": email, "exp": expiration_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def get_token_data(token: str = Cookie(None)) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(id=str(payload.get("user_id")), role=str(payload.get("role")))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


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


def verify_token(email: str, token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        response_email = payload.get("email")
        expiration = payload.get("exp")
        if not response_email or not expiration:
            return False
        expiration_datetime = datetime.utcfromtimestamp(expiration)
        if expiration_datetime < datetime.utcnow():
            return False
        return response_email == email
    except jwt.JWTError:
        return False


def get_current_user(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.id


def get_current_user_role(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.role
