import uuid
from enum import Enum

from sqlalchemy import TIMESTAMP, Column, Date, Float, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Role(Enum):
    STUDENT = "student"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(ENUM(Role.ADMIN.value, Role.STUDENT.value, name='role_enum'), nullable=False, default=Role.STUDENT)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    attendance_records = relationship("Attendance", back_populates="user")

class Event(Base):
    __tablename__ = "events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    location = Column(String, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    attendance_records = relationship("Attendance", back_populates="event")

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.event_id'), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="attendance_records")
    event = relationship("Event", back_populates="attendance_records")