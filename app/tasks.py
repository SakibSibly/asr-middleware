"""
Celery tasks for async processing
"""

from celery import Celery
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Meeting, Transcript, TranscriptSegment, ProcessingStatus, Language
from app.services.storage import StorageService
from app.services.asr import ASRService
from app.services.translation import TranslationService
from app.services.fireflies import FirefliesService

# Initialize Celery
celery_app = Celery(
    "asr_middleware",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Database session for tasks
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize services
storage_service = StorageService()
asr_service = ASRService()
translation_service = TranslationService()
fireflies_service = FirefliesService()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@celery_app.task(name="process_meeting_audio")
def process_meeting_audio(meeting_id: str):
    """
    Process meeting audio file
    1. Transcribe audio (ASR)
    2. Detect language per segment
    3. Translate Bengali segments to English
    """
    db = SessionLocal()
    
    try:
        # Get meeting
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            print(f"Meeting {meeting_id} not found")
            return
        
        # Update status
        meeting.status = ProcessingStatus.PROCESSING
        meeting.meeting_metadata["progress"] = 10
        meeting.meeting_metadata["status_message"] = "Starting transcription..."
        db.commit()
        
        # Get audio file path
        audio_path = storage_service.get_file_path(meeting.audio_file_path)
        
        # Detect language
        print(f"Detecting language for meeting {meeting_id}...")
        detected_lang = asr_service.detect_language(audio_path)
        print(f"Detected language: {detected_lang}")
        
        meeting.meeting_metadata["progress"] = 20
        meeting.meeting_metadata["detected_language"] = detected_lang
        db.commit()
        
        # Transcribe audio
        print(f"Transcribing meeting {meeting_id}...")
        transcription_result = asr_service.transcribe(
            audio_path,
            language=detected_lang if detected_lang in ["bn", "en"] else None,
        )
        
        meeting.meeting_metadata["progress"] = 60
        meeting.meeting_metadata["status_message"] = "Transcription completed, saving segments..."
        db.commit()
        
        # Create transcript record
        transcript = Transcript(
            meeting_id=meeting_id,
            language=Language(transcription_result["language"]),
            text=transcription_result["text"],
            processed_by=transcription_result["provider"],
            confidence_score=transcription_result.get("confidence"),
        )
        db.add(transcript)
        db.commit()
        
        # Create segments
        segments_to_translate = []
        for segment_data in transcription_result["segments"]:
            segment = TranscriptSegment(
                transcript_id=transcript.id,
                speaker_id=segment_data.get("speaker_id"),
                speaker_name=segment_data.get("speaker_name"),
                start_time=segment_data["start_time"],
                end_time=segment_data["end_time"],
                original_text=segment_data["text"],
                original_language=Language(segment_data.get("language", transcription_result["language"])),
                confidence_score=segment_data.get("confidence"),
            )
            db.add(segment)
            
            # Collect Bengali segments for translation
            if segment.original_language == Language.BENGALI:
                segments_to_translate.append(segment)
        
        db.commit()
        
        meeting.meeting_metadata["progress"] = 70
        meeting.meeting_metadata["status_message"] = "Translating Bengali segments..."
        db.commit()
        
        # Translate Bengali segments
        if segments_to_translate:
            print(f"Translating {len(segments_to_translate)} Bengali segments...")
            for i, segment in enumerate(segments_to_translate):
                try:
                    translation_result = translation_service.translate(
                        text=segment.original_text,
                        source_lang="bn",
                        target_lang="en",
                    )
                    
                    segment.translated_text = translation_result["text"]
                    segment.translation_service = translation_result["service"]
                    
                    # Update progress
                    progress = 70 + int((i + 1) / len(segments_to_translate) * 20)
                    meeting.meeting_metadata["progress"] = progress
                    db.commit()
                
                except Exception as e:
                    print(f"Translation failed for segment {segment.id}: {str(e)}")
        
        # Mark as completed
        meeting.status = ProcessingStatus.COMPLETED
        meeting.meeting_metadata["progress"] = 100
        meeting.meeting_metadata["status_message"] = "Processing completed successfully"
        db.commit()
        
        print(f"Meeting {meeting_id} processed successfully")
    
    except Exception as e:
        print(f"Error processing meeting {meeting_id}: {str(e)}")
        
        # Mark as failed
        meeting.status = ProcessingStatus.FAILED
        meeting.meeting_metadata["error"] = str(e)
        meeting.meeting_metadata["status_message"] = f"Processing failed: {str(e)}"
        db.commit()
    
    finally:
        db.close()


@celery_app.task(name="process_fireflies_meeting")
def process_fireflies_meeting(meeting_id: str):
    """
    Process meeting from Fireflies.ai
    1. Download audio from Fireflies
    2. Process with ASR pipeline
    """
    db = SessionLocal()
    
    try:
        # Get meeting
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            print(f"Meeting {meeting_id} not found")
            return
        
        meeting.status = ProcessingStatus.PROCESSING
        meeting.meeting_metadata["progress"] = 5
        meeting.meeting_metadata["status_message"] = "Downloading audio from Fireflies..."
        db.commit()
        
        # Download audio if URL is available
        if meeting.audio_file_url:
            audio_path = f"{storage_service.local_path}/{meeting_id}.audio"
            fireflies_service.download_audio(meeting.audio_file_url, audio_path)
            meeting.audio_file_path = audio_path
            db.commit()
        
        # Process with regular audio pipeline
        process_meeting_audio(meeting_id)
    
    except Exception as e:
        print(f"Error processing Fireflies meeting {meeting_id}: {str(e)}")
        
        meeting.status = ProcessingStatus.FAILED
        meeting.meeting_metadata["error"] = str(e)
        db.commit()
    
    finally:
        db.close()
