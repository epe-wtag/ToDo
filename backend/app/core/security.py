from datetime import datetime, timedelta
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.security import HTTPBearer
from jose import jwt

from app.core.config import settings
from app.model.base_model import User
from app.schema.auth_schema import TokenData
from app.util.hash import async_hash_password, verify_password
from logger import log

app = FastAPI()


bearer_scheme = HTTPBearer()


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return async_hash_password(password)


def create_access_token(data: dict, secret_key: str = settings.SECRET_KEY) -> str:
    expire = datetime.now(tz=datetime.timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def generate_verification_token(email: str) -> str:
    expiration_time = datetime.now(tz=datetime.timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"email": email, "exp": expiration_time}
    token = jwt.encode(payload, settings.VERIFICATION_KEY, algorithm=ALGORITHM)
    return token


def verify_old_password(user: User, old_password: str) -> None:
    if not verify_password(old_password, user.password):
        log.warning(f"Invalid old password for user_id: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Password"
        )


def get_token_data(
    token: Optional[str] = Cookie("token", secure=True, httponly=True),
    response: Response = None,
) -> TokenData:
    if not token or token == "token" or token is None:
        if response is not None:
            response.delete_cookie("id")
            response.delete_cookie("is_admin")
            response.headers.update({"WWW-Authenticate": "Bearer"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing",
                headers=response.headers,
            )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
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
    expiration_time = datetime.now(tz=datetime.timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"email": email, "exp": expiration_time}
    token = jwt.encode(payload, settings.RESET_PASSWORD_KEY, algorithm=ALGORITHM)
    return token


def verify_token(email: str, token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.VERIFICATION_KEY, algorithms=[ALGORITHM])
        response_email = payload.get("email")
        expiration = payload.get("exp")
        if not response_email or not expiration:
            return False
        expiration_datetime = datetime.fromtimestamp(expiration, tz=datetime.timezone.utc)
        if expiration_datetime < datetime.now(tz=datetime.timezone.utc):
            return False
        return response_email == email
    except jwt.JWTError:
        return False


def verify_reset_token(email: str, token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.RESET_PASSWORD_KEY, algorithms=[ALGORITHM])
        response_email = payload.get("email")
        expiration = payload.get("exp")

        if response_email != email:
            return False

        if expiration < datetime.now(tz=datetime.timezone.utc).timestamp():
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
