import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.routers import attendance, auth, event, websocket
from app.services.occupancy_detection import compute_occupancy_periodically


@asynccontextmanager
async def lifespan(app: FastAPI):
    occupancy_task = asyncio.create_task(compute_occupancy_periodically())
    yield
    occupancy_task.cancel()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:8000",  # Allow the frontend to access the backend
    "http://localhost:3000",  # Add any other frontend URL you need to allow
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins if set to ["*"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Register routers
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(event.router, prefix="/event", tags=["event"])
app.include_router(websocket.router, tags=["websocket"])

@app.get("/")
async def get():
    return {"message": "Welcome to the Seat Sense Server!"}
