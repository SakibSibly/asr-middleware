"""
SQLAlchemy database models
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class ProcessingStatus(str, enum.Enum):
    """Meeting processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, enum.Enum):
    """Supported languages"""
    BENGALI = "bn"
    ENGLISH = "en"
    MIXED = "mixed"


class Meeting(Base):
    """Meeting model"""
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    date_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    participants = Column(JSON, default=list)  # List of participant names
    audio_file_url = Column(String(1000), nullable=True)
    audio_file_path = Column(String(1000), nullable=True)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    meeting_metadata = Column("metadata", JSON, default=dict)
    fireflies_meeting_id = Column(String(100), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="meeting", cascade="all, delete-orphan")


class Transcript(Base):
    """Transcript model"""
    __tablename__ = "transcripts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    language = Column(Enum(Language), nullable=False)
    text = Column(Text, nullable=False)
    processed_by = Column(String(100), nullable=True)  # Service used (whisper, assemblyai, etc.)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="transcripts")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    """Transcript segment model (timestamped chunks)"""
    __tablename__ = "transcript_segments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transcript_id = Column(String, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(String(100), nullable=True)
    speaker_name = Column(String(200), nullable=True)
    start_time = Column(Float, nullable=False)  # Seconds
    end_time = Column(Float, nullable=False)  # Seconds
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)  # NULL if already English
    original_language = Column(Enum(Language), nullable=False)
    confidence_score = Column(Float, nullable=True)
    translation_service = Column(String(100), nullable=True)
    segment_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="segments")
    translations = relationship("Translation", back_populates="segment", cascade="all, delete-orphan")


class Translation(Base):
    """Translation model (tracks translation history)"""
    __tablename__ = "translations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    segment_id = Column(String, ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False)
    source_language = Column(Enum(Language), nullable=False)
    target_language = Column(Enum(Language), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    translation_service = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)  # Allow multiple translations, mark active one
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    segment = relationship("TranscriptSegment", back_populates="translations")


class ProcessingJob(Base):
    """Track async processing jobs"""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(50), nullable=False)  # transcription, translation, etc.
    celery_task_id = Column(String(100), nullable=True)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
