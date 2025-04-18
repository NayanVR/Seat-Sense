import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.token_manager import (UserTokenModel, create_access_token,
                                    decode_access_token, get_user_from_header)
from app.db import get_db
from app.models import User
from app.schema.auth import (ForgotPasswordRequest, ForgotPasswordResponse,
                             LoginRequest, LoginResponse, ProfileRequest,
                             ProfileResponse, RegisterFaceResponse,
                             ResetPasswordRequest, ResetPasswordResponse,
                             SignupRequest, SignupResponse)

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == req.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="Email does not exist")

        if not bcrypt.checkpw(req.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Password is incorrect")

        access_token = create_access_token(
            data=UserTokenModel(
                email=user.email,
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
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == req.email))
        user = result.scalar_one_or_none()

        if user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email,
            password=hashed_password.decode('utf-8'),
            role=req.role,
            face_verified=False
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Include role and other user details in the access token
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
        raise http_exc

    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/profile", response_model=ProfileResponse)
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
        raise HTTPException(status_code=500, detail="Internal server error")

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
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded_user = await decode_access_token(req.token)

        if decoded_user is None:
            raise HTTPException(status_code=401, detail="Token is invalid")

        fetched_user = await db.execute(select(User).filter(User.email == decoded_user.email))
        user = fetched_user.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())

        await db.execute(update(User).where(User.email == user.email).values(password=hashed_password.decode('utf-8')))
        await db.commit()

        return {"message": "Password reset successful"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during reset-password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import File, UploadFile


@router.post("/register-face", response_model=RegisterFaceResponse)
async def verify_face(
    user: UserTokenModel = Depends(get_user_from_header),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...)
):
    try:
        image_data = await file.read()
        # TODO: Implement face recognition logic here
        # Update the user's face_verified field in the database
        await db.execute(
            update(User)
            .where(User.user_id == user.user_id)
            .values(face_verified=True)
        )
        await db.commit()

        return {"message": "Face verified successfully", "face_verified": True}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during face verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")