"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatusEnum(str, Enum):
    """Processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LanguageEnum(str, Enum):
    """Language codes"""
    BENGALI = "bn"
    ENGLISH = "en"
    MIXED = "mixed"


# Meeting Schemas
class MeetingCreate(BaseModel):
    """Create meeting request"""
    title: str = Field(..., min_length=1, max_length=500)
    date_time: Optional[datetime] = None
    duration: Optional[int] = None
    participants: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MeetingUpdate(BaseModel):
    """Update meeting request"""
    title: Optional[str] = None
    duration: Optional[int] = None
    participants: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MeetingResponse(BaseModel):
    """Meeting response"""
    id: str
    title: str
    date_time: datetime
    duration: Optional[int]
    participants: List[str]
    audio_file_url: Optional[str]
    status: ProcessingStatusEnum
    metadata: Dict[str, Any]
    fireflies_meeting_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MeetingList(BaseModel):
    """Meeting list response"""
    meetings: List[MeetingResponse]
    total: int
    page: int
    page_size: int


# Transcript Schemas
class TranscriptSegmentResponse(BaseModel):
    """Transcript segment response"""
    id: str
    speaker_id: Optional[str]
    speaker_name: Optional[str]
    start_time: float
    end_time: float
    original_text: str
    translated_text: Optional[str]
    original_language: LanguageEnum
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    """Transcript response"""
    id: str
    meeting_id: str
    language: LanguageEnum
    text: str
    processed_by: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime
    segments: List[TranscriptSegmentResponse] = []
    
    class Config:
        from_attributes = True


# Translation Schemas
class TranslationRequest(BaseModel):
    """Translation request"""
    segment_id: str
    target_language: LanguageEnum = LanguageEnum.ENGLISH
    service: Optional[str] = None  # indictrans2, gpt-4, google, deepl


class TranslationResponse(BaseModel):
    """Translation response"""
    id: str
    segment_id: str
    source_language: LanguageEnum
    target_language: LanguageEnum
    source_text: str
    translated_text: str
    translation_service: str
    confidence_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Processing Schemas
class ProcessingStatusResponse(BaseModel):
    """Processing status response"""
    meeting_id: str
    status: ProcessingStatusEnum
    progress: int
    message: Optional[str]


class AudioUploadResponse(BaseModel):
    """Audio upload response"""
    meeting_id: str
    file_path: str
    file_url: Optional[str]
    file_size: int


# Fireflies Webhook Schemas
class FirefliesWebhookPayload(BaseModel):
    """Fireflies.ai webhook payload"""
    event: str
    meeting_id: str
    title: Optional[str]
    date: Optional[str]
    duration: Optional[int]
    transcript_url: Optional[str]
    audio_url: Optional[str]
    participants: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]


# Export Schemas
class ExportFormat(str, Enum):
    """Export format options"""
    TXT = "txt"
    JSON = "json"
    SRT = "srt"
    VTT = "vtt"
    DOCX = "docx"


class ExportRequest(BaseModel):
    """Export request"""
    meeting_id: str
    format: ExportFormat
    include_translations: bool = True
    include_timestamps: bool = True


# Admin Schemas
class SystemStats(BaseModel):
    """System statistics"""
    total_meetings: int
    total_transcripts: int
    total_translations: int
    processing_queue_size: int
    storage_used_mb: float
    avg_processing_time: float


class ServiceHealth(BaseModel):
    """Service health status"""
    database: str
    redis: str
    celery: str
    storage: str
