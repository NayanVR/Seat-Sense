import os

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings

current_directory = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_directory, ".env")

if load_dotenv(dotenv_path=dotenv_path):
    print(".env file loaded successfully")
else:
    print("Failed to load .env file")

_mail_config = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_USERNAME"),
    MAIL_PORT=587,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER=os.path.join(current_directory, "templates"),
)

class Settings(BaseSettings):
    password_reset_token_expires_minutes: int = 5
    token_expires_minutes: int = 10080  # 7 days
    token_algorithm: str = "HS256"
    token_secret_key: str = os.getenv('TOKEN_SECRET_KEY')
    # database_url: str = os.getenv('DATABASE_URL')
    async_database_url: str = os.getenv('ASYNC_DATABASE_URL')
    audi_latitude: float = 0
    audi_longitude: float = 0
    radius: float = 100
    ssim_threshold: float = 0.45
    edge_threshold: float = 15
    mail_config: ConnectionConfig = _mail_config

settings = Settings()