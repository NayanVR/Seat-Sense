import bcrypt
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger
from sqlalchemy import select
from app.core.token_manager import UserTokenModel, create_access_token, get_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

router = APIRouter()

@router.post("/login")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == login_data.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="Email does not exist")
    
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Password is incorrect")

        access_token = create_access_token(data=UserTokenModel(first_name=user.first_name, last_name=user.last_name, email=user.email))
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500)

@router.post("/signup")
async def signup(signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == signup_data.email))
        user = result.scalar_one_or_none()

        if user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = bcrypt.hashpw(signup_data.password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            first_name=signup_data.first_name,
            last_name=signup_data.last_name,
            email=signup_data.email,
            password=hashed_password.decode('utf-8')
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        access_token = create_access_token(data=UserTokenModel(first_name=user.first_name, last_name=user.last_name, email=user.email))

        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/profile")
async def profile(token: str, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user(token)
        return user

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error during profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")