# ASR Middleware - Bengali + English Meeting Transcription System

A comprehensive FastAPI-based middleware that extends Fireflies.ai with robust multi-lingual (Bengali + English) meeting transcription, translation, and storage capabilities.

## Features

- 🎙️ **Multi-lingual ASR**: Supports Bengali and English transcription using Whisper, Google Speech-to-Text, and AssemblyAI
- 🌐 **Translation**: Automatic Bengali → English translation using IndicTrans2, Google Translate, and OpenAI GPT
- 🔗 **Fireflies.ai Integration**: Webhook support and API integration for seamless meeting sync
- 👥 **Speaker Diarization**: Identify and label different speakers in meetings
- 📤 **Multiple Export Formats**: TXT, JSON, SRT, VTT, and DOCX
- ⚡ **Async Processing**: Celery-based task queue for background processing
- 💾 **Flexible Storage**: Local filesystem or AWS S3 for audio files
- 📊 **Admin Dashboard**: System monitoring and management endpoints

## Architecture

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── dependencies.py      # Dependency injection
│   ├── tasks.py             # Celery async tasks
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── meetings.py      # Meeting management
│   │   ├── transcripts.py   # Transcript endpoints
│   │   ├── translations.py  # Translation endpoints
│   │   ├── webhooks.py      # Fireflies webhook
│   │   └── exports.py       # Export functionality
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asr.py           # ASR service integration
│   │   ├── translation.py   # Translation services
│   │   ├── storage.py       # File storage
│   │   ├── fireflies.py     # Fireflies API client
│   │   └── export.py        # Export service
│   └── internal/
│       ├── __init__.py
│       └── admin.py         # Admin endpoints
├── .env                     # Environment variables
├── .env.example             # Example environment file
├── pyproject.toml           # Project dependencies (uv)
├── run.py                   # Development server
└── celery_worker.py         # Celery worker

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis server
- uv package manager

### 2. Installation

```bash
# Clone the repository
cd asr-middleware

# Install dependencies with uv
uv sync

# Or install manually
uv pip install -e .
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
# Minimum required:
# - DATABASE_URL
# - REDIS_URL
# - OPENAI_API_KEY (for Whisper)
```

### 4. Database Setup

```bash
# The database tables will be created automatically on first run
# Or you can use Alembic for migrations (recommended for production)
```

### 5. Run Services

```bash
# Terminal 1: Start FastAPI server
uv run python run.py
# or
uv run uvicorn app.main:app --reload

# Terminal 2: Start Celery worker
uv run celery -A celery_worker worker --loglevel=info

# Terminal 3 (Optional): Start Celery beat for scheduled tasks
uv run celery -A celery_worker beat --loglevel=info
```

### 6. Test API

```bash
# Health check
curl http://localhost:8000/health

# Create a meeting
curl -X POST http://localhost:8000/api/meetings/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Team Meeting", "participants": ["John", "Jane"]}'
```

## API Endpoints

### Meetings
- `POST /api/meetings/` - Create a meeting
- `GET /api/meetings/` - List meetings
- `GET /api/meetings/{id}` - Get meeting details
- `PATCH /api/meetings/{id}` - Update meeting
- `DELETE /api/meetings/{id}` - Delete meeting
- `POST /api/meetings/{id}/upload-audio` - Upload audio file
- `POST /api/meetings/{id}/process` - Trigger processing
- `GET /api/meetings/{id}/status` - Get processing status

### Transcripts
- `GET /api/transcripts/meeting/{meeting_id}` - Get meeting transcripts
- `GET /api/transcripts/meeting/{meeting_id}/segments` - Get segments
- `GET /api/transcripts/{transcript_id}` - Get transcript by ID

### Translations
- `POST /api/translations/translate` - Translate a segment
- `GET /api/translations/segment/{segment_id}/history` - Translation history
- `POST /api/translations/segment/{segment_id}/retranslate` - Retry translation

### Exports
- `GET /api/exports/meeting/{meeting_id}/{format}` - Export transcript (txt, json, srt, vtt, docx)

### Webhooks
- `POST /api/webhooks/fireflies` - Fireflies webhook endpoint
- `POST /api/webhooks/fireflies/sync` - Manual sync from Fireflies
- `GET /api/webhooks/fireflies/meetings` - List Fireflies meetings

### Admin
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/health` - Service health check
- `POST /api/admin/cleanup/failed-meetings` - Clean up failed meetings
- `POST /api/admin/reprocess/{meeting_id}` - Reprocess meeting

## Configuration Options

### ASR Providers
- **Whisper (OpenAI)**: Best for Bengali, open-source, runs locally or via API
- **Google Speech-to-Text**: Excellent Bengali support, cloud-based
- **AssemblyAI**: Good accuracy with built-in diarization

### Translation Providers
- **IndicTrans2**: Specialized for Indian languages (recommended for Bengali)
- **Google Translate**: Fast and reliable
- **OpenAI GPT-4**: Context-aware, high quality
- **DeepL**: Natural-sounding translations

### Storage Options
- **Local Filesystem**: Simple, no additional services needed
- **AWS S3**: Scalable, cloud storage with CDN support

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Format code
uv run black app/

# Lint code
uv run ruff check app/

# Run tests (if implemented)
uv run pytest
```

## Production Deployment

### Using Docker (Recommended)

```dockerfile
# See WORKFLOW.md for complete Docker setup
```

### Manual Deployment

1. Set up PostgreSQL and Redis
2. Configure environment variables
3. Use gunicorn or uvicorn with workers
4. Set up Celery workers with supervisord
5. Configure nginx as reverse proxy
6. Set up SSL certificates

## Cost Estimates

For 100 hours of meetings per month:
- **Whisper (self-hosted)**: $50-100/month (GPU compute)
- **Google Speech**: ~$144/month
- **Translation**: $20-200/month depending on provider
- **Infrastructure**: $100-300/month (hosting, database, storage)
- **Total**: ~$500-1,200/month

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check DATABASE_URL in .env
2. **Celery not processing**: Ensure Redis is running
3. **Whisper out of memory**: Use smaller model or add more RAM
4. **Translation fails**: Verify API keys are correct

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:
- Check WORKFLOW.md for detailed documentation
- Review the code comments
- Open an issue on GitHub

---

**Last Updated**: February 2, 2026
