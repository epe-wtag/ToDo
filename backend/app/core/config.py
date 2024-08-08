import os
import traceback

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from logger import log
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

load_dotenv()

#load and manage application configuration from environment variables
class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)
    
    DB_HOST: str = os.getenv("DB_HOST")
    DB_HOST_LOCAL: str = os.getenv("DB_HOST_local")
    DB_DATABASE: str = os.getenv("DB_DATABASE")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    MAIL_USERNAME: str =os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str =os.getenv("PASS")
    MAIL_FROM: str =os.getenv("MAIL_FROM")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    VERIFICATION_KEY: str = os.getenv("VERIFICATION_KEY")
    RESET_PASSWORD_KEY: str = os.getenv("RESET_PASSWORD_KEY")


settings = Settings()


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://0.0.0.0",
    "http://0.0.0.0:3000",
    "http://0.0.0.0:8000",
]


def cors_middleware(app):
    return CORSMiddleware(
        app,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

#inherits from BaseHTTPMiddleware, it catches unhandled exceptions during HTTP request processing and logs them
class LogExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            log.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
            return Response("Internal server error", status_code=500)
