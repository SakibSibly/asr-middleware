"""
Fireflies.ai webhook integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
import hmac
import hashlib

from app.dependencies import get_db, verify_api_key
from app.schemas import FirefliesWebhookPayload
from app.models import Meeting, ProcessingStatus
from app.config import settings
from app.services.fireflies import FirefliesService
from app.tasks import process_fireflies_meeting

router = APIRouter()
fireflies_service = FirefliesService()


def verify_fireflies_signature(payload: bytes, signature: str) -> bool:
    """Verify Fireflies webhook signature"""
    if not settings.FIREFLIES_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured
    
    expected_signature = hmac.new(
        settings.FIREFLIES_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/fireflies")
async def fireflies_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for Fireflies.ai notifications
    Receives notifications when a meeting is recorded and processed
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Fireflies-Signature", "")
    
    # Verify signature
    if not verify_fireflies_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    # Parse payload
    try:
        payload = FirefliesWebhookPayload.model_validate_json(body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}",
        )
    
    # Handle different event types
    if payload.event == "meeting.completed":
        # Check if meeting already exists
        existing_meeting = db.query(Meeting).filter(
            Meeting.fireflies_meeting_id == payload.meeting_id
        ).first()
        
        if existing_meeting:
            # Update existing meeting
            existing_meeting.status = ProcessingStatus.PENDING
            existing_meeting.audio_file_url = payload.audio_url
            existing_meeting.meeting_metadata = payload.metadata or {}
            db.commit()
            meeting_id = existing_meeting.id
        else:
            # Create new meeting record
            meeting = Meeting(
                title=payload.title or "Fireflies Meeting",
                participants=payload.participants or [],
                duration=payload.duration,
                fireflies_meeting_id=payload.meeting_id,
                audio_file_url=payload.audio_url,
                status=ProcessingStatus.PENDING,
                meeting_metadata=payload.metadata or {},
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            meeting_id = meeting.id
        
        # Trigger async processing
        background_tasks.add_task(process_fireflies_meeting, meeting_id)
        
        return {
            "status": "accepted",
            "meeting_id": meeting_id,
            "message": "Meeting processing queued",
        }
    
    elif payload.event == "meeting.started":
        return {
            "status": "acknowledged",
            "message": "Meeting start notification received",
        }
    
    else:
        return {
            "status": "ignored",
            "message": f"Unknown event type: {payload.event}",
        }


@router.post("/fireflies/sync")
async def sync_fireflies_meetings(
    background_tasks: BackgroundTasks,
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Manually sync recent meetings from Fireflies.ai
    """
    if not settings.FIREFLIES_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fireflies API key not configured",
        )
    
    # Fetch recent meetings from Fireflies
    meetings_data = await fireflies_service.get_recent_meetings(limit=limit)
    
    synced_meetings = []
    
    for meeting_data in meetings_data:
        # Check if meeting already exists
        existing_meeting = db.query(Meeting).filter(
            Meeting.fireflies_meeting_id == meeting_data["id"]
        ).first()
        
        if not existing_meeting:
            # Create new meeting
            meeting = Meeting(
                title=meeting_data["title"],
                participants=meeting_data.get("participants", []),
                duration=meeting_data.get("duration"),
                fireflies_meeting_id=meeting_data["id"],
                audio_file_url=meeting_data.get("audio_url"),
                status=ProcessingStatus.PENDING,
                metadata=meeting_data.get("metadata", {}),
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            synced_meetings.append(meeting.id)
            
            # Queue for processing
            background_tasks.add_task(process_fireflies_meeting, meeting.id)
    
    return {
        "status": "success",
        "synced_count": len(synced_meetings),
        "meeting_ids": synced_meetings,
    }


@router.get("/fireflies/meetings")
async def list_fireflies_meetings(
    limit: int = 20,
    api_key: str = Depends(verify_api_key),
):
    """
    List recent meetings from Fireflies.ai
    """
    if not settings.FIREFLIES_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fireflies API key not configured",
        )
    
    meetings = await fireflies_service.get_recent_meetings(limit=limit)
    
    return {
        "meetings": meetings,
        "total": len(meetings),
    }
