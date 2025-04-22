from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.token_manager import UserTokenModel, get_user_from_header
from app.db import get_db
from app.models import Event, Role
from app.schema.event import (EventCreateRequest, EventIdRequest,
                              EventListResponse, EventResponse,
                              EventUpdateRequest)

router = APIRouter()


@router.post("/create", response_model=EventResponse)
async def create_event(
    req: EventCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        new_event = Event(
            name=req.name,
            description=req.description,
            date=req.date,
            location=req.location,
            start_time=req.start_time,
            end_time=req.end_time
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)

        return EventResponse(
            event_id=str(new_event.event_id),
            name=new_event.name,
            description=new_event.description,
            date=new_event.date,
            location=new_event.location,
            start_time=new_event.start_time,
            end_time=new_event.end_time,
            created_at=new_event.created_at.isoformat(),
            updated_at=new_event.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get", response_model=EventResponse)
async def get_event(
    req: EventIdRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Event).filter(Event.event_id == req.event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventResponse(
            event_id=str(event.event_id),
            name=event.name,
            description=event.description,
            date=event.date,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/list", response_model=EventListResponse)
async def list_events(
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(Event))
        events = result.scalars().all()
        if not events:
            raise HTTPException(status_code=404, detail="No events found")
        return EventListResponse(
            events=[
                EventResponse(
                    event_id=str(event.event_id),
                    name=event.name,
                    description=event.description,
                    date=event.date,
                    location=event.location,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    created_at=event.created_at.isoformat(),
                    updated_at=event.updated_at.isoformat(),
                ) for event in events
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update", response_model=EventResponse)
async def update_event(
    req: EventUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        result = await db.execute(select(Event).filter(Event.event_id == req.event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Update event fields
        event.name = req.name or event.name
        event.description = req.description or event.description
        event.date = req.date or event.date
        event.location = req.location or event.location
        event.start_time = req.start_time or event.start_time
        event.end_time = req.end_time or event.end_time

        await db.commit()
        await db.refresh(event)
        return EventResponse(
            event_id=str(event.event_id),
            name=event.name,
            description=event.description,
            date=event.date,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
async def delete_event(
    req: EventIdRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        result = await db.execute(select(Event).filter(Event.event_id == req.event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        await db.execute(delete(Event).where(Event.event_id == req.event_id))
        await db.commit()
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))