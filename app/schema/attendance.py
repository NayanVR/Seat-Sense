from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MarkAttendanceRequest(BaseModel):
    user_id: str
    event_id: str
    latitude: float
    longitude: float

class MarkAttendanceResponse(BaseModel):
    message: str

class AttendanceByEventResponse(BaseModel):
    user_id: str
    event_id: str
    latitude: Optional[float]
    longitude: Optional[float]
    time: datetime

class DeleteAttendanceResponse(BaseModel):
    message: str