from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class EventIdRequest(BaseModel):
    event_id: str

class EventCreateRequest(BaseModel):
    name: str
    description: Optional[str]
    date: date
    location: Optional[str]
    start_time: Optional[time]
    end_time: Optional[time]

class EventUpdateRequest(BaseModel):
    event_id: str
    name: Optional[str]
    description: Optional[str]
    date: Optional[date]
    location: Optional[str]
    start_time: Optional[time]
    end_time: Optional[time]

class EventResponse(BaseModel):
    event_id: str
    name: str
    description: Optional[str]
    date: date
    location: Optional[str]
    start_time: Optional[time]
    end_time: Optional[time]
    created_at: str
    updated_at: str

class EventListResponse(BaseModel):
    events: list[EventResponse]