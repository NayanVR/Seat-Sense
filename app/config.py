import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    token_expires_minutes: int = 10080  # 7 days
    token_algorithm: str = "HS256"
    token_secret_key: str = os.getenv('TOKEN_SECRET_KEY')
    # database_url: str = os.getenv('DATABASE_URL')
    async_database_url: str = os.getenv('ASYNC_DATABASE_URL')
    ssim_threshold: float = 0.45
    edge_threshold: float = 15

settings = Settings()