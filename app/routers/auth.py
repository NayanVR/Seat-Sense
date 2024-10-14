import bcrypt
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy import select, update
from app.core.token_manager import UserTokenModel, create_access_token, decode_access_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import User

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class ProfileRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == req.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="Email does not exist")
    
        if not bcrypt.checkpw(req.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Password is incorrect")

        access_token = create_access_token(data=UserTokenModel(email=user.email))
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500)

@router.post("/signup")
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
            password=hashed_password.decode('utf-8')
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        access_token = create_access_token(data=UserTokenModel(email=user.email))

        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/profile")
async def profile(req: ProfileRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded_user = await decode_access_token(req.token)

        if decoded_user is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        fetched_user = await db.execute(select(User).filter(User.email == decoded_user.email))
        user = fetched_user.scalar_one_or_none()
        return user

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/forgot-password")
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

@router.post("/reset-password")
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