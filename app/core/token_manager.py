import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from fastapi.logger import logger
from jose import ExpiredSignatureError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import User


class UserTokenModel(BaseModel):
    email: str
    role: str
    first_name: str
    last_name: str
    user_id: str

async def decode_access_token(token: str) -> UserTokenModel:
    try:
        payload = jwt.decode(token, settings.token_secret_key, algorithms=settings.token_algorithm)
        user_data = payload.get("sub")
        user = UserTokenModel(**json.loads(user_data))
        return user

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except Exception as e:
        logger.error(f"JWT decoding error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(data: UserTokenModel, expires_delta_minutes: timedelta = None) -> UserTokenModel:
    to_encode = {}
    to_encode.update({"sub": data.model_dump_json()})
    try:
        if expires_delta_minutes:
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expires_minutes)

        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, settings.token_secret_key, algorithm=settings.token_algorithm)
    except Exception as e:
        logger.error(f"Error during token creation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_user_from_header(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    user = await decode_access_token(authorization.split(" ")[1])
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user