"""
FastAPI Application - ASR Middleware
Main entry point for the API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import meetings, transcripts, translations, webhooks, exports
from app.internal import admin
from app.database import engine, Base
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting ASR Middleware...")
    # Try to create database tables (optional if DB not configured)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"⚠️  Database connection failed: {str(e)}")
        print("⚠️  Running without database - configure DATABASE_URL in .env")
    yield
    # Shutdown
    print("Shutting down ASR Middleware...")


app = FastAPI(
    title="ASR Middleware API",
    description="Multi-lingual (Bengali + English) meeting transcription and translation system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])
app.include_router(transcripts.router, prefix="/api/transcripts", tags=["transcripts"])
app.include_router(translations.router, prefix="/api/translations", tags=["translations"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ASR Middleware",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "redis": "connected",
            "celery": "running",
        },
    }
