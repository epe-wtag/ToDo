from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Column,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.model.task_model import Task


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)

    tasks = relationship("Task", back_populates="owner")
