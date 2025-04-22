import io
import pdb
from typing import Annotated, List, Tuple

import face_recognition
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.logger import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.location_manager import verify_inside_audi_within_radius
from app.core.token_manager import UserTokenModel, get_user_from_header
from app.db import get_db
from app.models import Attendance, Event, FaceEmbedding, Role, User
from app.schema.attendance import (AttendanceByEventRequest,
                                   AttendanceByEventResponse,
                                   DeleteAttendanceRequest,
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
    event_id: Annotated[str, Form()],
    longitude: Annotated[float, Form()],
    latitude: Annotated[float, Form()],
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    image_file = await image.read()
    if not image_file:
        raise HTTPException(status_code=400, detail="Failed to read image file")

    # Process image and detect faces in one section
    try:
        # TODO: Uncomment this line to verify if the user is within the required radius
        # if not verify_inside_audi_within_radius(latitude, longitude):
        #     raise HTTPException(status_code=403, detail="User is not within the required radius")

        image_data = face_recognition.load_image_file(io.BytesIO(image_file))
        face_encodings = face_recognition.face_encodings(image_data)

        if not face_encodings:
            raise HTTPException(status_code=400, detail="No face detected")

        query_embedding = face_encodings[0]

        # Optimize database query - fetch user embeddings in one query
        result = await db.execute(
            select(FaceEmbedding.embedding)
            .filter(FaceEmbedding.user_id == user.user_id)
        )
        user_embeddings = result.scalars().all()

        if not user_embeddings:
            raise HTTPException(status_code=404, detail="No face embeddings found for the user")

        # Optimize face comparison by using batch processing
        # Convert database embeddings to a list of arrays for batch comparison
        db_embedding_arrays = [embedding for embedding in user_embeddings]
        matches = face_recognition.compare_faces(db_embedding_arrays, query_embedding, tolerance=0.6)

        if not any(matches):
            raise HTTPException(status_code=403, detail="Forbidden: No matching face found for the user")

        # Check if event exists using get or 404 pattern
        event = await db.execute(select(Event).filter(Event.event_id == event_id))
        event = event.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

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
        logger.error(f"Error marking attendance from image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/by-event", response_model=List[AttendanceByEventResponse])
async def get_attendance_by_event(
    req: AttendanceByEventRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        # Get all attendance records for the event
        result = await db.execute(select(Attendance, User).join(User, Attendance.user_id == User.user_id).filter(Attendance.event_id == req.event_id))
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
    req: DeleteAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    user: UserTokenModel = Depends(get_user_from_header)
):
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: Admin role required")
    try:
        # Delete the attendance record
        result = await db.execute(delete(Attendance).where(Attendance.attendance_id == req.attendance_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        await db.commit()
        return {"message": "Attendance record deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
