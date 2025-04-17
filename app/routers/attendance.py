from typing import List, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.token_manager import UserTokenModel, get_user_from_header
from app.db import get_db
from app.models import Attendance, Event, Role, User
from app.schema.attendance import (AttendanceByEventResponse,
                                   DeleteAttendanceResponse,
                                   MarkAttendanceRequest,
                                   MarkAttendanceResponse)

router = APIRouter()

@router.post("/mark", response_model=MarkAttendanceResponse)
async def mark_attendance(
    req: MarkAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")

    try:
        # Check if the event exists
        event = await db.execute(select(Event).filter(Event.event_id == req.event_id))
        event = event.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Check if the user exists
        user_record = await db.execute(select(User).filter(User.user_id == req.user_id))
        user_record = user_record.scalar_one_or_none()
        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        # Mark attendance
        attendance = Attendance(
            user_id=req.user_id,
            event_id=req.event_id,
            latitude=req.latitude,
            longitude=req.longitude
        )
        db.add(attendance)
        await db.commit()
        return {"message": "Attendance marked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-from-image", response_model=MarkAttendanceResponse)
async def mark_attendance_from_image(
    event_id: str,
    image: UploadFile = File(...),
    latitude: float = None,
    longitude: float = None,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    try:
        # Skip face recognition logic for now
        # TODO: Assume user info is obtained from the auth token

        # Check if the event exists
        event = await db.execute(select(Event).filter(Event.event_id == event_id))
        event = event.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Mark attendance
        attendance = Attendance(
            user_id=user.user_id,
            event_id=event_id,
            latitude=latitude,
            longitude=longitude
        )
        db.add(attendance)
        await db.commit()
        return {"message": "Attendance marked successfully from image"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/by-event", response_model=List[AttendanceByEventResponse])
async def get_attendance_by_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        # Get all attendance records for the event
        result = await db.execute(select(Attendance, User).join(User, Attendance.user_id == User.user_id).filter(Attendance.event_id == event_id))
        attendance_records: List[Tuple[Attendance, User]] = result.all()

        if not attendance_records:
            raise HTTPException(status_code=404, detail="No attendance records found for this event")

        return [
            {
                "attendance_id": attendance.attendance_id,
                "user_id": user.user_id,
                "event_id": attendance.event_id,
                "latitude": attendance.latitude,
                "longitude": attendance.longitude
            } for attendance, user in attendance_records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete", response_model=DeleteAttendanceResponse)
async def delete_attendance(
    attendance_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        # Delete the attendance record
        result = await db.execute(delete(Attendance).where(Attendance.attendance_id == attendance_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        await db.commit()
        return {"message": "Attendance record deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
