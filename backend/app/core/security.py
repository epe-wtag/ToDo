import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Response

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt
from pydantic import EmailStr
from starlette.responses import JSONResponse

from app.model.base_model import User
from app.schema.auth_schema import TokenData
from fastapi.responses import RedirectResponse
from logger import log

from app.util.hash import async_hash_password, verify_password

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


async def hash_password(password: str) -> str:
    return await async_hash_password(password)


def create_access_token(data: dict, secret_key: str = SECRET_KEY) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def generate_verification_token(email: str) -> str:
    expiration_time = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"email": email, "exp": expiration_time}
    token = jwt.encode(payload, VERIFICATION_KEY, algorithm=ALGORITHM)
    return token


async def verify_old_password(user: User, old_password: str) -> None:
    if not verify_password(old_password, user.password):
        log.warning(f"Invalid old password for user_id: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Password"
        )


def get_token_data(
    token: Optional[str] = Cookie("token", secure=True, httponly=True),
    response: Response = None
) -> TokenData:
    if not token or token == 'token' or token is None:
        if response is not None:
            response.delete_cookie('id')
            response.delete_cookie('is_admin')
            response.headers.update({"WWW-Authenticate": "Bearer"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing",
                headers=response.headers,
            )

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


def generate_reset_token(email: str) -> str:
    expiration_time = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"email": email, "exp": expiration_time}
    token = jwt.encode(payload, RESET_PASSWORD_KEY, algorithm=ALGORITHM)
    return token


async def send_reset_email(email: EmailStr, token: str) -> JSONResponse:
    html = f"""
    <html>
      <head></head>
      <body>
        <p>Hello,</p>
        <p>You have requested to reset your password. Please click the link below to reset your password:</p>
        <p><a style="background-color: #008CBA; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;"
        href="http://localhost:3000/reset-password/{email}/{token}">Reset Password</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>
      </body>
    </html>
    """

    message = MessageSchema(
        subject="Reset Password",
        recipients=[email],
        body=html,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})


def verify_token(email: str, token: str) -> bool:
    try:
        payload = jwt.decode(token, VERIFICATION_KEY, algorithms=[ALGORITHM])
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


def verify_reset_token(email: str, token: str) -> bool:
    try:
        payload = jwt.decode(token, RESET_PASSWORD_KEY, algorithms=[ALGORITHM])
        response_email = payload.get("email")
        expiration = payload.get("exp")

        if response_email != email:
            return False

        if expiration < datetime.utcnow().timestamp():
            return False

        return True

    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


def get_current_user(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.id


def get_current_user_role(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.role
