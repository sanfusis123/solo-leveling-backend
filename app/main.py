from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

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
    title="Solo Leveling API",
    description="A comprehensive backend API for tracking personal development, time management, and learning progress",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
# Parse allowed origins from environment variable
origins = []
if settings.ALLOWED_ORIGINS:
    origins = [origin.strip().rstrip('/') for origin in settings.ALLOWED_ORIGINS.split(',') if origin.strip()]

# Add common development origins if not in production
if 'localhost' in str(origins):
    origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ])

print(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add root endpoint
@app.get("/")
async def root():
    return {
        "message": "Solo Leveling API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-cors")
async def test_cors():
    return {
        "message": "CORS test successful",
        "allowed_origins": origins,
        "timestamp": str(datetime.now())
    }

# Include API router
app.include_router(api_router, prefix="/api/v1")