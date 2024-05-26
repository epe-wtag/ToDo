import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.v1.routes import routers as v1_routers
from app.core.config import LogExceptionsMiddleware, cors_middleware
from app.db.database import create_all_tables
from logger import log

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


app = FastAPI()


app.add_middleware(cors_middleware)

app.add_middleware(LogExceptionsMiddleware)


if not os.getenv("TESTING"):
    Path("/logs").mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    await create_all_tables()


@app.get("/")
def root():
    log.info("Root endpoint called")
    return "To-Do is working"


app.include_router(v1_routers, prefix="/api/v1")
