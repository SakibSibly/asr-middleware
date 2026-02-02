"""
Meeting management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.dependencies import get_db, verify_api_key
from app.schemas import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingList,
    ProcessingStatusResponse,
    AudioUploadResponse,
)
from app.models import Meeting, ProcessingStatus
from app.services.storage import StorageService
from app.tasks import process_meeting_audio

router = APIRouter()
storage_service = StorageService()


@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_db),
):
    """Create a new meeting"""
    db_meeting = Meeting(
        title=meeting.title,
        date_time=meeting.date_time,
        duration=meeting.duration,
        participants=meeting.participants,
        meeting_metadata=meeting.metadata,
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


@router.get("/", response_model=MeetingList)
async def list_meetings(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all meetings with pagination"""
    query = db.query(Meeting)
    
    if status_filter:
        query = query.filter(Meeting.status == status_filter)
    
    total = query.count()
    meetings = query.offset(skip).limit(limit).all()
    
    return {
        "meetings": meetings,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
    }


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    """Get meeting details by ID"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_update: MeetingUpdate,
    db: Session = Depends(get_db),
):
    """Update meeting details"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    update_data = meeting_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(meeting, key, value)
    
    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    """Delete a meeting and all associated data"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    # Delete audio file if exists
    if meeting.audio_file_path:
        storage_service.delete_file(meeting.audio_file_path)
    
    db.delete(meeting)
    db.commit()
    return None


@router.post("/{meeting_id}/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload audio file for a meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    # Validate file type
    allowed_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".webm"]
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )
    
    # Save file
    file_path, file_url = await storage_service.save_audio_file(
        audio_file, meeting_id
    )
    
    # Update meeting record
    meeting.audio_file_path = file_path
    meeting.audio_file_url = file_url
    meeting.status = ProcessingStatus.PENDING
    db.commit()
    
    # Trigger async processing
    background_tasks.add_task(process_meeting_audio, meeting_id)
    
    return {
        "meeting_id": meeting_id,
        "file_path": file_path,
        "file_url": file_url,
        "file_size": audio_file.size or 0,
    }


@router.post("/{meeting_id}/process", response_model=ProcessingStatusResponse)
async def trigger_processing(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger meeting processing"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    if not meeting.audio_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded for this meeting",
        )
    
    if meeting.status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is already being processed",
        )
    
    meeting.status = ProcessingStatus.PROCESSING
    db.commit()
    
    # Trigger async processing
    background_tasks.add_task(process_meeting_audio, meeting_id)
    
    return {
        "meeting_id": meeting_id,
        "status": ProcessingStatus.PROCESSING,
        "progress": 0,
        "message": "Processing started",
    }


@router.get("/{meeting_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    """Get processing status for a meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    return {
        "meeting_id": meeting_id,
        "status": meeting.status,
        "progress": meeting.meeting_metadata.get("progress", 0),
        "message": meeting.meeting_metadata.get("status_message", ""),
    }
