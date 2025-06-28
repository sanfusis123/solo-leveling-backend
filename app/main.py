from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import connect_to_database, close_database_connection
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_database()
    yield
    # Shutdown
    await close_database_connection()

app = FastAPI(
    title="Personal Development Tracker",
    description="A comprehensive backend API for tracking personal development, time management, and learning progress",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
origins_str  = settings.ALLOWED_ORIGINS

origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

print("originsa:", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Personal Development Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}