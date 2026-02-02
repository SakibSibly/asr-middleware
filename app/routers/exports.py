"""
Export endpoints for transcripts
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import io
import json
from typing import Optional

from app.dependencies import get_db
from app.schemas import ExportFormat
from app.models import Meeting, Transcript, TranscriptSegment
from app.services.export import ExportService

router = APIRouter()
export_service = ExportService()


@router.get("/meeting/{meeting_id}/{format}")
async def export_meeting(
    meeting_id: str,
    format: ExportFormat,
    include_translations: bool = True,
    include_timestamps: bool = True,
    db: Session = Depends(get_db),
):
    """Export meeting transcript in various formats"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    
    # Get all segments
    segments = db.query(TranscriptSegment).join(Transcript).filter(
        Transcript.meeting_id == meeting_id
    ).order_by(TranscriptSegment.start_time).all()
    
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transcript segments found for this meeting",
        )
    
    # Export based on format
    if format == ExportFormat.TXT:
        content = export_service.export_txt(
            segments, include_translations, include_timestamps
        )
        media_type = "text/plain"
        filename = f"{meeting.title}_transcript.txt"
    
    elif format == ExportFormat.JSON:
        content = export_service.export_json(
            meeting, segments, include_translations
        )
        media_type = "application/json"
        filename = f"{meeting.title}_transcript.json"
    
    elif format == ExportFormat.SRT:
        content = export_service.export_srt(segments, include_translations)
        media_type = "text/plain"
        filename = f"{meeting.title}_subtitles.srt"
    
    elif format == ExportFormat.VTT:
        content = export_service.export_vtt(segments, include_translations)
        media_type = "text/vtt"
        filename = f"{meeting.title}_subtitles.vtt"
    
    elif format == ExportFormat.DOCX:
        # For DOCX, we need to return a file
        file_path = export_service.export_docx(
            meeting, segments, include_translations, include_timestamps
        )
        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{meeting.title}_transcript.docx",
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}",
        )
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(content.encode() if isinstance(content, str) else content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
