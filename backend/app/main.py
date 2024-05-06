from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.config import cors_middleware
from app.core.database import create_all_tables

from app.api.v1.routes import routers as v1_routers

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

