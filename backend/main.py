from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

from app.api.v1.routes import routers as v1_routers
from app.core.config import LogExceptionsMiddleware, cors_middleware
from app.db.database import create_all_tables

logger.add(
    "caselog.log",
    rotation="200 MB",
    level="INFO",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
)


load_dotenv()

app = FastAPI()

app.add_middleware(cors_middleware)
app.add_middleware(LogExceptionsMiddleware)


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return "To-Do is working"


class Startup:
    async def on_startup(self):
        await create_all_tables


app.include_router(v1_routers, prefix="/api/v1")
