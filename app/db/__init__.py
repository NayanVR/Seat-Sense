# from sqlalchemy import create_engine
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

# Dependency to get the database session
async def get_db():
    async with SessionLocal() as session:
        yield session