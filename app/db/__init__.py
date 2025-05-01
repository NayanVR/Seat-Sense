import os
import sqlite3

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create an async engine
engine = create_async_engine(settings.async_database_url, echo=True)

# Create the async sessionmaker
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,  # Use AsyncSession for async capabilities
    autocommit=False,
    autoflush=False
)

async def get_db():
    async with SessionLocal() as session:
        yield session

db_file_path = os.path.join(os.path.dirname(__file__), "otp_database.sqlite")

otp_db = sqlite3.connect(db_file_path)  # Connect to the SQLite database file
otp_db.row_factory = sqlite3.Row  # Optional: Access rows as dictionaries
cur = otp_db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS otps (
    email TEXT PRIMARY KEY,
    otp INTEGER
)
""")
otp_db.commit()
cur.close()

def get_otp_db() -> sqlite3.Connection:
    return otp_db