from datetime import datetime, timedelta, timezone
import json
from fastapi import HTTPException
from fastapi.logger import logger
from jose import ExpiredSignatureError, jwt
from pydantic import BaseModel
from app.config import settings

class UserTokenModel(BaseModel):
    first_name: str
    last_name: str
    email: str

async def get_user(token: str):
    try:
        payload = jwt.decode(token, settings.token_secret_key, algorithms=settings.token_algorithm)
        user_data = payload.get("sub")
        user = UserTokenModel(**json.loads(user_data))
        return user
    
    except ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    
    except Exception as e:
        logger.error(f"JWT decoding error: {e}")
        return None

def create_access_token(data: UserTokenModel, expires_delta: timedelta = None):
    to_encode = {}
    to_encode.update({"sub": data.model_dump_json()})
    try:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expires_minutes)
        
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, settings.token_secret_key, algorithm=settings.token_algorithm)
    except Exception as e:
        logger.error(f"Error during token creation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")