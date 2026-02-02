"""
Dependency injection for FastAPI routes
"""

from typing import Generator
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.config import settings


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key for protected endpoints"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


async def verify_webhook_signature(
    x_webhook_signature: str = Header(...),
) -> str:
    """Verify webhook signature from Fireflies.ai"""
    # Implement signature verification logic
    if not x_webhook_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )
    return x_webhook_signature


def get_current_user():
    """Get current authenticated user (placeholder for future implementation)"""
    # TODO: Implement JWT authentication
    return {"user_id": "admin", "role": "admin"}
