# ASR Middleware - Implementation Guide

## Quick Implementation Steps

### Step 1: Update Dependencies

Add to `pyproject.toml`:
```toml
[project]
dependencies = [
    "django>=5.2.10",
    "djangorestframework>=3.16.1",
    "celery>=5.4.0",
    "redis>=5.0.0",
    "openai-whisper>=20231117",
    "google-cloud-speech>=2.26.0",
    "google-cloud-translate>=3.15.0",
    "assemblyai>=0.25.0",
    "pydub>=0.25.1",
    "librosa>=0.10.1",
    "pyannote.audio>=3.1.1",
    "torch>=2.1.0",
    "transformers>=4.36.0",
    "langdetect>=1.0.9",
    "boto3>=1.34.0",
    "python-decouple>=3.8",
    "psycopg2-binary>=2.9.9",
    "django-cors-headers>=4.9.0",
    "djangorestframework-simplejwt>=5.5.1",
    "drf-spectacular>=0.29.0",
    "requests>=2.31.0",
    "python-dateutil>=2.8.2",
    "sentry-sdk>=1.40.0",
]
```

### Step 2: Project Structure

```
asr-middleware/
├── core/                          # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py                 # NEW
│   └── wsgi.py
├── meetings/                      # Main app
│   ├── __init__.py
│   ├── models.py                 # Meeting, Transcript, TranscriptSegment
│   ├── serializers.py            # DRF serializers
│   ├── views.py                  # API views
│   ├── urls.py                   # App URLs
│   ├── tasks.py                  # Celery tasks
│   ├── admin.py                  # Django admin
│   └── tests.py
├── services/                      # Business logic
│   ├── __init__.py
│   ├── audio_processor.py        # Audio preprocessing
│   ├── asr_service.py            # ASR integration
│   ├── translation_service.py    # Translation integration
│   ├── fireflies_service.py      # Fireflies.ai API
│   ├── storage_service.py        # File storage (S3)
│   └── language_detector.py      # Language detection
├── utils/                         # Utilities
│   ├── __init__.py
│   ├── constants.py
│   ├── exceptions.py
│   └── helpers.py
├── static/                        # Static files
├── media/                         # Uploaded files
├── requirements.txt               # Generated from pyproject.toml
├── .env.example                   # Example environment variables
├── WORKFLOW.md                    # Workflow documentation
├── IMPLEMENTATION.md              # This file
└── README.md
```

### Step 3: Environment Setup

Create `.env` file:
```bash
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/asr_middleware

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 (or use local storage for development)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1

# Fireflies.ai
FIREFLIES_API_KEY=your-fireflies-api-key
FIREFLIES_WEBHOOK_SECRET=your-webhook-secret

# OpenAI (Whisper API)
OPENAI_API_KEY=your-openai-api-key

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id

# AssemblyAI
ASSEMBLYAI_API_KEY=your-assemblyai-key

# Translation
GOOGLE_TRANSLATE_API_KEY=your-google-translate-key

# Monitoring
SENTRY_DSN=

# Processing settings
MAX_AUDIO_SIZE_MB=500
WHISPER_MODEL=large-v3
ENABLE_SPEAKER_DIARIZATION=True
ENABLE_AUTO_TRANSLATION=True
```

### Step 4: Database Models

File: `meetings/models.py`
```python
from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class Meeting(models.Model):
    """Main meeting record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in seconds", null=True, blank=True)
    participants = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    audio_file = models.FileField(upload_to='meetings/%Y/%m/', null=True, blank=True)
    audio_url = models.URLField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fireflies_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_time']
        indexes = [
            models.Index(fields=['-date_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.date_time}"


class Transcript(models.Model):
    """Complete transcript for a meeting"""
    LANGUAGE_CHOICES = [
        ('bn', 'Bengali'),
        ('en', 'English'),
        ('mixed', 'Mixed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='transcripts')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    text = models.TextField()
    processed_by = models.CharField(max_length=100, help_text="ASR service used")
    processing_time = models.FloatField(help_text="Processing time in seconds", null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transcript ({self.language}) - {self.meeting.title}"


class TranscriptSegment(models.Model):
    """Individual transcript segments with speaker and timing info"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='segments')
    speaker_id = models.CharField(max_length=50, null=True, blank=True)
    speaker_name = models.CharField(max_length=100, null=True, blank=True)
    
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    
    original_text = models.TextField()
    original_language = models.CharField(max_length=10)
    
    translated_text = models.TextField(null=True, blank=True)
    translation_service = models.CharField(max_length=100, null=True, blank=True)
    
    confidence_score = models.FloatField(null=True, blank=True)
    translation_confidence = models.FloatField(null=True, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['transcript', 'start_time']),
            models.Index(fields=['original_language']),
        ]
    
    def __str__(self):
        return f"Segment {self.start_time}s-{self.end_time}s"


class Translation(models.Model):
    """Track translations for quality and auditing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    segment = models.ForeignKey(TranscriptSegment, on_delete=models.CASCADE, related_name='translations')
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    source_text = models.TextField()
    translated_text = models.TextField()
    translation_service = models.CharField(max_length=100)
    confidence_score = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.source_language} → {self.target_language}"


class ProcessingJob(models.Model):
    """Track processing jobs for monitoring"""
    JOB_TYPES = [
        ('transcription', 'Transcription'),
        ('translation', 'Translation'),
        ('diarization', 'Speaker Diarization'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    celery_task_id = models.CharField(max_length=100, null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting', 'job_type']),
            models.Index(fields=['status']),
        ]
```

### Step 5: Celery Configuration

File: `core/celery.py`
```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('asr_middleware')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'sync-fireflies-meetings': {
        'task': 'meetings.tasks.sync_fireflies_meetings',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-jobs': {
        'task': 'meetings.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

Update `core/__init__.py`:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Step 6: API Serializers

File: `meetings/serializers.py`
```python
from rest_framework import serializers
from .models import Meeting, Transcript, TranscriptSegment, Translation, ProcessingJob


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = TranscriptSegment
        fields = [
            'id', 'speaker_id', 'speaker_name',
            'start_time', 'end_time', 'duration',
            'original_text', 'original_language',
            'translated_text', 'translation_service',
            'confidence_score', 'translation_confidence',
            'metadata'
        ]
    
    def get_duration(self, obj):
        return obj.end_time - obj.start_time


class TranscriptSerializer(serializers.ModelSerializer):
    segments = TranscriptSegmentSerializer(many=True, read_only=True)
    segment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Transcript
        fields = [
            'id', 'meeting', 'language', 'text',
            'processed_by', 'processing_time',
            'created_at', 'segments', 'segment_count'
        ]
    
    def get_segment_count(self, obj):
        return obj.segments.count()


class ProcessingJobSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'meeting', 'job_type', 'status',
            'started_at', 'completed_at', 'duration',
            'error_message', 'metadata', 'created_at'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class MeetingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'date_time', 'duration',
            'participant_count', 'status',
            'created_at', 'updated_at'
        ]
    
    def get_participant_count(self, obj):
        return len(obj.participants) if obj.participants else 0


class MeetingDetailSerializer(serializers.ModelSerializer):
    transcripts = TranscriptSerializer(many=True, read_only=True)
    jobs = ProcessingJobSerializer(many=True, read_only=True)
    audio_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'date_time', 'duration',
            'participants', 'audio_file', 'audio_file_url',
            'audio_url', 'status', 'fireflies_id',
            'metadata', 'created_at', 'updated_at',
            'transcripts', 'jobs'
        ]
    
    def get_audio_file_url(self, obj):
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
        return None


class MeetingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            'title', 'date_time', 'duration',
            'participants', 'audio_file', 'audio_url',
            'metadata'
        ]


class AudioUploadSerializer(serializers.Serializer):
    audio_file = serializers.FileField()
    
    def validate_audio_file(self, value):
        # Validate file size
        max_size = 500 * 1024 * 1024  # 500 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size must not exceed {max_size // (1024*1024)}MB"
            )
        
        # Validate file type
        valid_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.mp4']
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in valid_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(valid_extensions)}"
            )
        
        return value
```

### Step 7: Core Services Implementation

File: `services/asr_service.py`
```python
import whisper
import os
from typing import Dict, List, Tuple
from decouple import config
import logging

logger = logging.getLogger(__name__)


class ASRService:
    """Automatic Speech Recognition Service"""
    
    def __init__(self):
        self.whisper_model = config('WHISPER_MODEL', default='large-v3')
        self.model = None
    
    def load_whisper_model(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.whisper_model}")
            self.model = whisper.load_model(self.whisper_model)
        return self.model
    
    def transcribe_with_whisper(
        self, 
        audio_path: str, 
        language: str = None
    ) -> Dict:
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (bn, en, or None for auto-detect)
        
        Returns:
            Dict with transcription results
        """
        try:
            model = self.load_whisper_model()
            
            logger.info(f"Transcribing {audio_path} with Whisper (language: {language})")
            
            result = model.transcribe(
                audio_path,
                language=language,
                task='transcribe',
                verbose=False,
                word_timestamps=True
            )
            
            return {
                'success': True,
                'text': result['text'],
                'language': result['language'],
                'segments': result['segments'],
                'service': f'whisper-{self.whisper_model}'
            }
        
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_bengali(self, audio_path: str) -> Dict:
        """Transcribe Bengali audio"""
        return self.transcribe_with_whisper(audio_path, language='bn')
    
    def transcribe_english(self, audio_path: str) -> Dict:
        """Transcribe English audio"""
        return self.transcribe_with_whisper(audio_path, language='en')
    
    def transcribe_auto(self, audio_path: str) -> Dict:
        """Auto-detect language and transcribe"""
        return self.transcribe_with_whisper(audio_path, language=None)
```

File: `services/translation_service.py`
```python
import openai
from google.cloud import translate_v2 as translate
from decouple import config
import logging

logger = logging.getLogger(__name__)


class TranslationService:
    """Translation service for Bengali to English"""
    
    def __init__(self):
        self.openai_key = config('OPENAI_API_KEY', default=None)
        self.google_translate_client = None
    
    def get_google_translate_client(self):
        """Get Google Translate client (lazy loading)"""
        if self.google_translate_client is None:
            self.google_translate_client = translate.Client()
        return self.google_translate_client
    
    def translate_with_gpt(
        self, 
        text: str, 
        source_lang: str = 'bn',
        target_lang: str = 'en',
        context: str = None
    ) -> Dict:
        """
        Translate text using OpenAI GPT
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Additional context for better translation
        
        Returns:
            Dict with translation results
        """
        try:
            if not self.openai_key:
                raise ValueError("OpenAI API key not configured")
            
            openai.api_key = self.openai_key
            
            prompt = f"Translate the following {'Bengali' if source_lang == 'bn' else source_lang} text to {'English' if target_lang == 'en' else target_lang}. Preserve technical terms and meeting context:\n\n{text}"
            
            if context:
                prompt = f"Context: {context}\n\n" + prompt
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in Bengali to English translation for business meetings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'translated_text': translated_text,
                'service': 'openai-gpt4',
                'source_language': source_lang,
                'target_language': target_lang
            }
        
        except Exception as e:
            logger.error(f"GPT translation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def translate_with_google(
        self,
        text: str,
        source_lang: str = 'bn',
        target_lang: str = 'en'
    ) -> Dict:
        """
        Translate text using Google Translate
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Dict with translation results
        """
        try:
            client = self.get_google_translate_client()
            
            result = client.translate(
                text,
                source_language=source_lang,
                target_language=target_lang
            )
            
            return {
                'success': True,
                'translated_text': result['translatedText'],
                'service': 'google-translate',
                'source_language': source_lang,
                'target_language': target_lang,
                'detected_language': result.get('detectedSourceLanguage')
            }
        
        except Exception as e:
            logger.error(f"Google translation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def translate(
        self,
        text: str,
        source_lang: str = 'bn',
        target_lang: str = 'en',
        method: str = 'google'
    ) -> Dict:
        """
        Translate text using specified method
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            method: Translation method ('google', 'gpt', 'auto')
        
        Returns:
            Dict with translation results
        """
        if method == 'gpt':
            return self.translate_with_gpt(text, source_lang, target_lang)
        elif method == 'google':
            return self.translate_with_google(text, source_lang, target_lang)
        elif method == 'auto':
            # Try Google first, fallback to GPT
            result = self.translate_with_google(text, source_lang, target_lang)
            if not result['success']:
                result = self.translate_with_gpt(text, source_lang, target_lang)
            return result
        else:
            raise ValueError(f"Unknown translation method: {method}")
```

### Step 8: Celery Tasks

File: `meetings/tasks.py`
```python
from celery import shared_task
from django.utils import timezone
from .models import Meeting, Transcript, TranscriptSegment, ProcessingJob
from services.asr_service import ASRService
from services.translation_service import TranslationService
from services.language_detector import LanguageDetector
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_meeting_audio(self, meeting_id):
    """
    Main task to process meeting audio
    - Transcribe audio
    - Detect languages
    - Translate non-English segments
    """
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        meeting.status = 'processing'
        meeting.save()
        
        # Create processing job
        job = ProcessingJob.objects.create(
            meeting=meeting,
            job_type='transcription',
            status='processing',
            started_at=timezone.now(),
            celery_task_id=self.request.id
        )
        
        # Get audio file path
        audio_path = meeting.audio_file.path if meeting.audio_file else None
        if not audio_path:
            raise ValueError("No audio file found")
        
        # Transcribe
        asr_service = ASRService()
        result = asr_service.transcribe_auto(audio_path)
        
        if not result['success']:
            raise Exception(f"Transcription failed: {result.get('error')}")
        
        # Create transcript
        transcript = Transcript.objects.create(
            meeting=meeting,
            language=result['language'],
            text=result['text'],
            processed_by=result['service']
        )
        
        # Create segments
        for segment in result['segments']:
            TranscriptSegment.objects.create(
                transcript=transcript,
                start_time=segment['start'],
                end_time=segment['end'],
                original_text=segment['text'],
                original_language=result['language'],
                confidence_score=segment.get('confidence', None)
            )
        
        # Trigger translation for Bengali segments
        if result['language'] == 'bn':
            translate_transcript.delay(transcript.id)
        
        # Update job and meeting
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        meeting.status = 'completed'
        meeting.save()
        
        logger.info(f"Meeting {meeting_id} processed successfully")
        return {'success': True, 'transcript_id': str(transcript.id)}
    
    except Exception as e:
        logger.error(f"Error processing meeting {meeting_id}: {str(e)}")
        
        if 'job' in locals():
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
        
        if 'meeting' in locals():
            meeting.status = 'failed'
            meeting.save()
        
        # Retry
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def translate_transcript(self, transcript_id):
    """Translate transcript segments"""
    try:
        transcript = Transcript.objects.get(id=transcript_id)
        translation_service = TranslationService()
        
        # Create processing job
        job = ProcessingJob.objects.create(
            meeting=transcript.meeting,
            job_type='translation',
            status='processing',
            started_at=timezone.now(),
            celery_task_id=self.request.id
        )
        
        segments = transcript.segments.filter(original_language='bn', translated_text__isnull=True)
        
        for segment in segments:
            result = translation_service.translate(
                segment.original_text,
                source_lang='bn',
                target_lang='en',
                method='auto'
            )
            
            if result['success']:
                segment.translated_text = result['translated_text']
                segment.translation_service = result['service']
                segment.save()
        
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Transcript {transcript_id} translated successfully")
        return {'success': True}
    
    except Exception as e:
        logger.error(f"Error translating transcript {transcript_id}: {str(e)}")
        
        if 'job' in locals():
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task
def sync_fireflies_meetings():
    """Periodic task to sync meetings from Fireflies.ai"""
    # Implementation depends on Fireflies API
    logger.info("Syncing meetings from Fireflies.ai")
    # TODO: Implement Fireflies API integration
    pass


@shared_task
def cleanup_old_jobs():
    """Clean up old processing jobs"""
    from datetime import timedelta
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count, _ = ProcessingJob.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    ).delete()
    logger.info(f"Cleaned up {deleted_count} old processing jobs")
    return deleted_count
```

---

## Next Steps

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Set up services**:
   - Install and start PostgreSQL
   - Install and start Redis
   - Configure environment variables

3. **Initialize database**:
   ```bash
   python manage.py makemigrations meetings
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start development servers**:
   ```bash
   # Terminal 1: Django
   python manage.py runserver
   
   # Terminal 2: Celery Worker
   celery -A core worker -l info
   
   # Terminal 3: Celery Beat
   celery -A core beat -l info
   ```

5. **Test the API**:
   - Upload a meeting: POST /api/meetings/
   - Upload audio: POST /api/meetings/{id}/upload-audio/
   - Trigger processing: POST /api/meetings/{id}/process/
   - Get transcript: GET /api/meetings/{id}/transcript/

---

See `WORKFLOW.md` for complete architecture and workflow documentation.
