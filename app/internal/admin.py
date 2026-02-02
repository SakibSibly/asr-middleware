"""
Admin endpoints for system management and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, verify_api_key
from app.schemas import SystemStats, ServiceHealth
from app.models import Meeting, Transcript, Translation, ProcessingStatus

router = APIRouter()


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Get system statistics"""
    total_meetings = db.query(Meeting).count()
    total_transcripts = db.query(Transcript).count()
    total_translations = db.query(Translation).count()
    
    # Count processing queue
    processing_queue = db.query(Meeting).filter(
        Meeting.status.in_([ProcessingStatus.PENDING, ProcessingStatus.PROCESSING])
    ).count()
    
    # Calculate average processing time (placeholder)
    avg_processing_time = 0.0
    
    # Calculate storage usage (placeholder)
    storage_used_mb = 0.0
    
    return {
        "total_meetings": total_meetings,
        "total_transcripts": total_transcripts,
        "total_translations": total_translations,
        "processing_queue_size": processing_queue,
        "storage_used_mb": storage_used_mb,
        "avg_processing_time": avg_processing_time,
    }


@router.get("/health", response_model=ServiceHealth)
async def check_service_health(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Check health of all services"""
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check Redis (placeholder)
    redis_status = "connected"
    
    # Check Celery (placeholder)
    celery_status = "running"
    
    # Check storage (placeholder)
    storage_status = "available"
    
    return {
        "database": db_status,
        "redis": redis_status,
        "celery": celery_status,
        "storage": storage_status,
    }


@router.post("/cleanup/failed-meetings")
async def cleanup_failed_meetings(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Clean up failed meeting records"""
    failed_meetings = db.query(Meeting).filter(
        Meeting.status == ProcessingStatus.FAILED
    ).all()
    
    count = len(failed_meetings)
    
    for meeting in failed_meetings:
        db.delete(meeting)
    
    db.commit()
    
    return {
        "status": "success",
        "deleted_count": count,
    }


@router.post("/reprocess/{meeting_id}")
async def reprocess_meeting(
    meeting_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Reprocess a failed meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    # Reset status to pending
    meeting.status = ProcessingStatus.PENDING
    db.commit()
    
    # Trigger processing (would normally use Celery)
    from app.tasks import process_meeting_audio
    process_meeting_audio(meeting_id)
    
    return {
        "status": "success",
        "meeting_id": meeting_id,
        "message": "Reprocessing started",
    }


@router.get("/meetings/processing")
async def get_processing_meetings(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Get all meetings currently being processed"""
    meetings = db.query(Meeting).filter(
        Meeting.status.in_([ProcessingStatus.PENDING, ProcessingStatus.PROCESSING])
    ).all()
    
    return {
        "meetings": [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
            }
            for m in meetings
        ],
        "total": len(meetings),
    }
