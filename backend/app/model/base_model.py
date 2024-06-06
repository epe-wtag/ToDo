from enum import Enum as PyEnum

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Category(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    contact_number = Column(String)
    gender = Column(String)
    is_active = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)

    tasks = relationship("Task", back_populates="owner")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    description = Column(String)
    status = Column(Boolean, default=False)
    due_date = Column(DateTime)
    delete_request = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    category = Column(Enum(Category), default=Category.LOW, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)

    owner = relationship("User", back_populates="tasks")
