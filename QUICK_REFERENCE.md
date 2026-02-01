# ASR Middleware - Quick Reference Guide

## 🚀 Quick Commands

### Development

```bash
# Start development server
python manage.py runserver

# Start Celery worker
celery -A core worker -l info

# Start Celery beat (scheduled tasks)
celery -A core beat -l info

# Monitor Celery tasks
celery -A core flower

# Run tests
python manage.py test

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Production

```bash
# Start with Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Check service status
sudo systemctl status asr-middleware
sudo systemctl status asr-celery
sudo systemctl status asr-celery-beat

# View logs
sudo journalctl -u asr-middleware -f
sudo journalctl -u asr-celery -f

# Restart services
sudo systemctl restart asr-middleware
sudo systemctl restart asr-celery
```

## 📝 Common API Usage

### Authentication

```bash
# Get token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/meetings/
```

### Create & Process Meeting

```bash
# 1. Create meeting
curl -X POST http://localhost:8000/api/meetings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "date_time": "2026-02-01T10:00:00Z"
  }'

# Response: {"id": "550e8400-e29b-41d4-a716-446655440000", ...}

# 2. Upload audio
curl -X POST http://localhost:8000/api/meetings/<id>/upload-audio/ \
  -H "Authorization: Bearer <token>" \
  -F "audio_file=@meeting.mp3"

# 3. Start processing
curl -X POST http://localhost:8000/api/meetings/<id>/process/ \
  -H "Authorization: Bearer <token>"

# 4. Check status
curl http://localhost:8000/api/meetings/<id>/status/ \
  -H "Authorization: Bearer <token>"

# 5. Get transcript
curl http://localhost:8000/api/meetings/<id>/transcript/ \
  -H "Authorization: Bearer <token>"
```

## 🔧 Configuration Quick Reference

### Essential Environment Variables

```bash
# Minimum required for development
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
```

### ASR Service Priority

1. Bengali: Whisper Large-v3 → Google Speech → AssemblyAI
2. English: Fireflies.ai → Whisper → AssemblyAI

### Translation Service Priority

1. Bengali→English: IndicTrans2 → GPT-4 → Google Translate

## 📊 Database Quick Reference

### Models Overview

```
Meeting
├── id (UUID)
├── title
├── date_time
├── status (pending/processing/completed/failed)
├── audio_file
└── metadata

Transcript
├── id (UUID)
├── meeting_id (FK)
├── language (bn/en/mixed)
├── text
└── processed_by

TranscriptSegment
├── id (UUID)
├── transcript_id (FK)
├── start_time
├── end_time
├── original_text
├── original_language
├── translated_text
└── speaker_id

ProcessingJob
├── id (UUID)
├── meeting_id (FK)
├── job_type (transcription/translation)
├── status (pending/processing/completed/failed)
└── celery_task_id
```

### Common Queries

```python
from meetings.models import Meeting, Transcript, TranscriptSegment

# Get all completed meetings
meetings = Meeting.objects.filter(status='completed')

# Get meeting with transcripts
meeting = Meeting.objects.prefetch_related('transcripts').get(id='...')

# Get Bengali segments needing translation
segments = TranscriptSegment.objects.filter(
    original_language='bn',
    translated_text__isnull=True
)

# Get failed jobs
failed_jobs = ProcessingJob.objects.filter(status='failed')
```

## 🐛 Debugging

### Check Celery Queue

```python
from celery import Celery
app = Celery('asr_middleware')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Inspect active tasks
i = app.control.inspect()
print(i.active())
print(i.scheduled())
print(i.reserved())
```

### Check Redis

```bash
# Connect to Redis
redis-cli

# Check queue
LLEN celery
KEYS *

# View task
LRANGE celery 0 -1
```

### View Celery Task

```python
from celery.result import AsyncResult
from core.celery import app

# Check task status
result = AsyncResult('task-id', app=app)
print(result.state)
print(result.info)
```

### Debug Processing Pipeline

```python
from services.asr_service import ASRService
from services.translation_service import TranslationService

# Test ASR
asr = ASRService()
result = asr.transcribe_with_whisper('audio.mp3', language='bn')
print(result)

# Test translation
translator = TranslationService()
result = translator.translate('আপনার নাম কি?', source_lang='bn', target_lang='en')
print(result)
```

## 🧪 Testing Quick Reference

### Run Specific Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test meetings

# Specific test class
python manage.py test meetings.tests.MeetingTestCase

# Specific test method
python manage.py test meetings.tests.MeetingTestCase.test_create_meeting

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test in Shell

```python
python manage.py shell

from django.test import Client
from django.contrib.auth.models import User

# Create test client
client = Client()

# Login
user = User.objects.create_user('test', 'test@example.com', 'testpass')
client.login(username='test', password='testpass')

# Test API
response = client.get('/api/meetings/')
print(response.status_code)
print(response.json())
```

## 📦 Dependency Management

### Update Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade django

# Regenerate requirements
pip freeze > requirements.txt
```

### Check for Updates

```bash
pip list --outdated
```

## 🔐 Security Quick Reference

### Generate Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Check Security

```bash
python manage.py check --deploy
```

### Update Passwords

```python
python manage.py changepassword <username>
```

## 📈 Performance Monitoring

### Django Debug Toolbar

```python
# Add to INSTALLED_APPS
INSTALLED_APPS += ['debug_toolbar']

# Add to MIDDLEWARE
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Configure
INTERNAL_IPS = ['127.0.0.1']
```

### Query Profiling

```python
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Your code here
    print(len(connection.queries))
    for query in connection.queries:
        print(query['sql'])
```

### Celery Monitoring

```bash
# Real-time monitoring
celery -A core events

# Inspect workers
celery -A core inspect active
celery -A core inspect stats
```

## 🔄 Data Management

### Backup Database

```bash
# PostgreSQL
pg_dump -U asruser -d asr_middleware > backup.sql

# With compression
pg_dump -U asruser -d asr_middleware | gzip > backup.sql.gz
```

### Restore Database

```bash
# PostgreSQL
psql -U asruser -d asr_middleware < backup.sql

# From compressed
gunzip -c backup.sql.gz | psql -U asruser -d asr_middleware
```

### Clean Old Data

```python
from django.utils import timezone
from datetime import timedelta
from meetings.models import Meeting, ProcessingJob

# Delete meetings older than 90 days
cutoff = timezone.now() - timedelta(days=90)
Meeting.objects.filter(created_at__lt=cutoff).delete()

# Clean completed jobs older than 30 days
cutoff = timezone.now() - timedelta(days=30)
ProcessingJob.objects.filter(
    status='completed',
    created_at__lt=cutoff
).delete()
```

## 🔧 Common Issues & Solutions

### Issue: "No audio file found"
**Solution**: Ensure audio_file is uploaded before processing
```python
meeting.audio_file  # Should not be None
```

### Issue: "Whisper model loading failed"
**Solution**: Download model manually
```python
import whisper
whisper.load_model("large-v3")  # Downloads to cache
```

### Issue: "Translation service unavailable"
**Solution**: Check API keys and fallback
```python
# Check configuration
print(os.getenv('OPENAI_API_KEY'))
print(os.getenv('GOOGLE_TRANSLATE_API_KEY'))
```

### Issue: "Celery tasks not running"
**Solution**: Check Redis connection
```bash
redis-cli ping  # Should return PONG
celery -A core inspect ping  # Check workers
```

### Issue: "Database connection failed"
**Solution**: Verify DATABASE_URL
```python
from django.db import connection
connection.ensure_connection()
```

## 📚 Useful Resources

### Documentation Links
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Celery: https://docs.celeryq.dev/
- Whisper: https://github.com/openai/whisper
- Fireflies API: https://docs.fireflies.ai/

### Code Examples Location
- Models: `meetings/models.py`
- Serializers: `meetings/serializers.py`
- Views: `meetings/views.py`
- Tasks: `meetings/tasks.py`
- Services: `services/*.py`

### Configuration Files
- Django settings: `core/settings.py`
- URL routing: `core/urls.py`, `meetings/urls.py`
- Celery config: `core/celery.py`
- Environment: `.env`

## 🎯 Best Practices

1. **Always use environment variables** for sensitive data
2. **Test locally** before deploying
3. **Use transactions** for database operations
4. **Log everything** (especially errors)
5. **Monitor Celery queues** regularly
6. **Back up database** before migrations
7. **Use versioning** for API endpoints
8. **Implement rate limiting** for public APIs
9. **Cache frequently** accessed data
10. **Document all changes**

## 🆘 Getting Help

1. Check logs: `sudo journalctl -u asr-middleware -f`
2. Review [WORKFLOW.md](WORKFLOW.md) for architecture
3. Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for code details
4. Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API usage
5. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues

---

**Pro Tip**: Bookmark this file for quick reference during development!
