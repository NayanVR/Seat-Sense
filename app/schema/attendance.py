from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MarkAttendanceRequest(BaseModel):
    email: str
    event_id: str

class MarkAttendanceResponse(BaseModel):
    message: str


class AttendanceByEventRequest(BaseModel):
    event_id: str

class AttendanceByEventResponse(BaseModel):
    attendance_id: str
    user_id: str
    first_name: str
    last_name: str
    email: str
    time: datetime


class DeleteAttendanceRequest(BaseModel):
    attendance_id: str

class DeleteAttendanceResponse(BaseModel):
    message: str