import traceback
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logger import log


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_HOST_LOCAL = os.getenv("DB_HOST_local")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
MAIL_USERNAME=os.getenv("EMAIL")
MAIL_PASSWORD=os.getenv("PASS")
MAIL_FROM=os.getenv("EMAIL")
SECRET_KEY = os.getenv("SECRET_KEY")
VERIFICATION_KEY = os.getenv("VERIFICATION_KEY")
RESET_PASSWORD_KEY = os.getenv("RESET_PASSWORD_KEY")




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


class LogExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            log.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
            return Response("Internal server error", status_code=500)
