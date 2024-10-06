import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, websocket
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
app.include_router(auth.router)
app.include_router(websocket.router)

@app.get("/")
async def get():
    return {"message": "Welcome to the Seat Sense Server!"}
