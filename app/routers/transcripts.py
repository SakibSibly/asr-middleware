"""
Transcript management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.schemas import TranscriptResponse, TranscriptSegmentResponse
from app.models import Meeting, Transcript, TranscriptSegment

router = APIRouter()


@router.get("/meeting/{meeting_id}", response_model=List[TranscriptResponse])
async def get_meeting_transcripts(
    meeting_id: str,
    db: Session = Depends(get_db),
):
    """Get all transcripts for a meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    transcripts = db.query(Transcript).filter(
        Transcript.meeting_id == meeting_id
    ).all()
    
    return transcripts


@router.get("/meeting/{meeting_id}/segments", response_model=List[TranscriptSegmentResponse])
async def get_meeting_segments(
    meeting_id: str,
    language: str = None,
    db: Session = Depends(get_db),
):
    """Get all transcript segments for a meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    query = db.query(TranscriptSegment).join(Transcript).filter(
        Transcript.meeting_id == meeting_id
    )
    
    if language:
        query = query.filter(TranscriptSegment.original_language == language)
    
    segments = query.order_by(TranscriptSegment.start_time).all()
    
    return segments


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: str,
    include_segments: bool = False,
    db: Session = Depends(get_db),
):
    """Get transcript by ID"""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found",
        )
    
    if include_segments:
        # Eager load segments
        segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.transcript_id == transcript_id
        ).order_by(TranscriptSegment.start_time).all()
        transcript.segments = segments
    
    return transcript


@router.get("/segment/{segment_id}", response_model=TranscriptSegmentResponse)
async def get_segment(
    segment_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific transcript segment"""
    segment = db.query(TranscriptSegment).filter(
        TranscriptSegment.id == segment_id
    ).first()
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )
    
    return segment
