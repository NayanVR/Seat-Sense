import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

current_directory = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_directory, ".env")

if load_dotenv(dotenv_path=dotenv_path):
    print(".env file loaded successfully")
else:
    print("Failed to load .env file")

class Settings(BaseSettings):
    password_reset_token_expires_minutes: int = 5
    token_expires_minutes: int = 10080  # 7 days
    token_algorithm: str = "HS256"
    token_secret_key: str = os.getenv('TOKEN_SECRET_KEY')
    # database_url: str = os.getenv('DATABASE_URL')
    async_database_url: str = os.getenv('ASYNC_DATABASE_URL')
    resend_api_key: str = os.getenv('RESEND_API_KEY')
    audi_latitude: float = 0
    audi_longitude: float = 0
    radius: float = 100
    ssim_threshold: float = 0.45
    edge_threshold: float = 15

settings = Settings()