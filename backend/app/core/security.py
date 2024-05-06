import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt

from app.schema.auth_schema import TokenData

load_dotenv()

bearer_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180


def create_access_token(data: dict, secret_key: str = SECRET_KEY) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


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


def get_current_user(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.id


def get_current_user_role(token_data: TokenData = Depends(get_token_data)) -> str:
    return token_data.role
