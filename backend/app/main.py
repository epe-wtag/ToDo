import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.v1.routes import routers as v1_routers
from app.core.config import cors_middleware
from app.core.database import create_all_tables

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


app = FastAPI()



app.add_middleware(cors_middleware)


@app.on_event("startup")
async def startup_event():
    await create_all_tables()


@app.get("/")
def root():
    return "To-Do is working"


app.include_router(v1_routers, prefix="/api/v1")
