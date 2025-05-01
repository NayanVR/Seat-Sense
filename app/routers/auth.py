import io
import random
import sqlite3

import bcrypt
import face_recognition
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, File, UploadFile
from fastapi.logger import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.token_manager import (UserTokenModel, create_access_token,
                                    decode_access_token, get_user_from_header)
from app.db import get_db, get_otp_db
from app.models import FaceEmbedding, Role, User
from app.schema.auth import (ForgotPasswordRequest, ForgotPasswordResponse,
                             LoginRequest, LoginResponse, ProfileResponse,
                             RegisterFaceResponse, ResetPasswordRequest,
                             ResetPasswordResponse, SendOTPRequest,
                             SignupRequest, SignupResponse, VerifyOTPRequest)
from app.services.resend_mail import send_otp_verification_email

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == req.email.lower()))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="Email does not exist")

        if not bcrypt.checkpw(req.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Password is incorrect")

        access_token = create_access_token(
            data=UserTokenModel(
                email=user.email.lower(),
                role=user.role,
                first_name=user.first_name,
                last_name=user.last_name,
                user_id=str(user.user_id),
                face_verified=user.face_verified
            )
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500)

@router.post("/signup", response_model=SignupResponse)
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db), otp_db: sqlite3.Connection = Depends(get_otp_db)):
    try:
        # Verify OTP
        cur = otp_db.cursor()
        result = cur.execute("SELECT otp FROM otps WHERE email = ?", (req.email.lower(),)).fetchone()

        print(f"User OTP: {req.otp} - DB OTP: {result[0] if result[0] else result}")

        if not result or result[0] != req.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Check if the user already exists
        existing_user = await db.execute(select(User).filter(User.email == req.email))
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already exists")

        # Hash the password and create the user
        hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email.lower(),
            password=hashed_password.decode('utf-8'),
            role=Role.STUDENT.value,
            face_verified=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        cur.execute("DELETE FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),))
        otp_db.commit()
        cur.close()

        # Generate access token
        access_token = create_access_token(
            data=UserTokenModel(
                email=new_user.email,
                role=new_user.role,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                user_id=str(new_user.user_id),
                face_verified=new_user.face_verified
            )
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500)

@router.post("/profile", response_model=ProfileResponse)
async def profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_user_from_header)):
    try:
        fetched_user = await db.execute(select(User).filter(User.email == user.email))
        user = fetched_user.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Return user details including role
        return {
            "user_id": str(user.user_id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "face_verified": user.face_verified,
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during profile: {e}")
        raise HTTPException(status_code=500)

@router.post("/send-otp", response_model=dict)
async def send_otp(req: SendOTPRequest, background_tasks: BackgroundTasks, otp_db: sqlite3.Connection = Depends(get_otp_db)):
    try:
        otp = random.randint(100000, 999999)

        cur = otp_db.cursor()
        result = cur.execute("SELECT otp FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),)).fetchone()

        if result:
            cur.execute("UPDATE otps SET otp = ? WHERE LOWER(email) = LOWER(?)", (otp, req.email.lower()))
        else:
            cur.execute("INSERT INTO otps (email, otp) VALUES (?, ?)", (req.email.lower(), otp))

        otp_db.commit()

        result = cur.execute("SELECT otp FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),)).fetchone()
        print(f"OTP for {req.email}: {result[0]}")
        cur.close()

        background_tasks.add_task(send_otp_verification_email, req.email, str(otp))

        return {"message": "OTP sent to your email"}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Error during send-otp: {e}")
        raise HTTPException(status_code=500)

@router.post("/verify-otp", response_model=dict)
async def verify_otp(req: VerifyOTPRequest, otp_db: sqlite3.Connection = Depends(get_otp_db)):
    try:
        cur = otp_db.cursor()
        result = cur.execute("SELECT otp FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),)).fetchone()

        if not result or result[0] != req.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        return {"message": "OTP verified successfully"}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Error during verify-otp: {e}")
        raise HTTPException(status_code=500)

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        fetched_user = await db.execute(select(User).filter(User.email == req.email))
        user = fetched_user.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        password_reset_token = create_access_token(data=UserTokenModel(email=user.email), expires_delta_minutes=settings.password_reset_token_expires_minutes)

        return {"password_reset_token": password_reset_token}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during forgot-password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db), otp_db: sqlite3.Connection = Depends(get_otp_db)):
    try:
        # Verify OTP
        cur = otp_db.cursor()
        result = cur.execute("SELECT otp FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),)).fetchone()

        if not result or result[0] != req.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Fetch the user
        fetched_user = await db.execute(select(User).filter(User.email == req.email.lower()))
        user = fetched_user.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Hash the new password
        hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())

        # Update the user's password
        await db.execute(update(User).where(User.email == user.email).values(password=hashed_password.decode('utf-8')))
        await db.commit()

        # Remove the OTP after successful password reset
        cur.execute("DELETE FROM otps WHERE LOWER(email) = LOWER(?)", (req.email.lower(),))
        otp_db.commit()
        cur.close()

        return {"message": "Password reset successful"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during reset-password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register-face", response_model=RegisterFaceResponse)
async def register_face(
    user: UserTokenModel = Depends(get_user_from_header),
    db: AsyncSession = Depends(get_db),
    image: UploadFile = File(...)
):
    try:
        image_file = await image.read()
        if not image_file:
            raise HTTPException(status_code=400, detail="Failed to read image file")

        image_data = io.BytesIO(image_file)

        image = face_recognition.load_image_file(image_data)
        face_encodings = face_recognition.face_encodings(image)

        if not face_encodings:
            raise HTTPException(status_code=400, detail="No face detected")

        embedding = face_encodings[0]

        new_embedding = FaceEmbedding(
            user_id=user.user_id,
            embedding=embedding
        )
        db.add(new_embedding)

        await db.execute(
            update(User)
            .where(User.user_id == user.user_id)
            .values(face_verified=True)
        )
        await db.commit()

        return {"message": "Face registered successfully", "face_verified": True}

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Unexpected error during face registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")