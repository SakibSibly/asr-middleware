# 🚀 Quick Start Guide - ASR Middleware

This guide will help you get the ASR Middleware up and running quickly.

## Prerequisites

- Python 3.11+ 
- PostgreSQL database server
- Redis server
- `uv` package manager ([installation guide](https://github.com/astral-sh/uv))

## Installation

### 1. Install uv (if not already installed)

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install PostgreSQL and Redis

**Windows:**
- PostgreSQL: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Redis: Use [Memurai](https://www.memurai.com/) or WSL2

**macOS (Homebrew):**
```bash
brew install postgresql redis
brew services start postgresql
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server
sudo systemctl start postgresql
sudo systemctl start redis
```

### 3. Clone and Setup Project

```bash
# Navigate to project directory
cd asr-middleware

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
```

### 4. Configure Environment

Edit `.env` file with your settings:

```bash
# Minimum configuration for testing
DATABASE_URL=postgresql://postgres:password@localhost:5432/asr_middleware
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-openai-key-here  # For Whisper
API_KEY=your-secret-api-key-here
```

### 5. Initialize Database

```bash
# Create database
createdb asr_middleware

# Initialize tables
uv run python init_db.py create
```

## Running the Application

### Development Mode (3 separate terminals)

**Terminal 1 - API Server:**
```bash
uv run python run.py
```

**Terminal 2 - Celery Worker:**
```bash
uv run celery -A celery_worker worker --loglevel=info
```

**Terminal 3 (Optional) - Celery Beat (for scheduled tasks):**
```bash
uv run celery -A celery_worker beat --loglevel=info
```

### Using Docker Compose (Recommended for Testing)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Testing the API

### 1. Access API Documentation

Open your browser and visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 2. Health Check

```bash
curl http://localhost:8000/health
```

### 3. Create a Meeting

```bash
curl -X POST http://localhost:8000/api/meetings/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Meeting",
    "participants": ["John Doe", "Jane Smith"]
  }'
```

### 4. Upload Audio File

```bash
# Save the meeting ID from previous response
MEETING_ID="your-meeting-id-here"

curl -X POST "http://localhost:8000/api/meetings/${MEETING_ID}/upload-audio" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@/path/to/your/audio.mp3"
```

### 5. Check Processing Status

```bash
curl http://localhost:8000/api/meetings/${MEETING_ID}/status
```

### 6. Get Transcript

```bash
curl http://localhost:8000/api/transcripts/meeting/${MEETING_ID}
```

## Common Commands

### Database Management

```bash
# Create tables
uv run python init_db.py create

# Drop all tables (CAUTION!)
uv run python init_db.py drop
```

### Celery Management

```bash
# Start worker
uv run celery -A celery_worker worker --loglevel=info

# Monitor tasks
uv run celery -A celery_worker events

# Purge all tasks
uv run celery -A celery_worker purge
```

### Code Formatting & Linting

```bash
# Format code
uv run black app/

# Lint code
uv run ruff check app/
```

## Project Structure

```
asr-middleware/
├── app/                    # Main application package
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── tasks.py           # Celery tasks
│   ├── routers/           # API route handlers
│   │   ├── meetings.py
│   │   ├── transcripts.py
│   │   ├── translations.py
│   │   ├── webhooks.py
│   │   └── exports.py
│   ├── services/          # Business logic
│   │   ├── asr.py
│   │   ├── translation.py
│   │   ├── storage.py
│   │   ├── fireflies.py
│   │   └── export.py
│   └── internal/          # Admin endpoints
│       └── admin.py
├── .env                   # Environment variables
├── pyproject.toml         # Project dependencies
├── run.py                 # Development server
├── celery_worker.py       # Celery worker entry
└── init_db.py            # Database initialization
```

## API Key Setup

### OpenAI (Required for Whisper)
1. Create account at [platform.openai.com](https://platform.openai.com/)
2. Generate API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Fireflies.ai (Optional)
1. Sign up at [fireflies.ai](https://fireflies.ai/)
2. Get API key from settings
3. Add to `.env`: `FIREFLIES_API_KEY=...`

### Google Cloud (Optional)
1. Create project at [console.cloud.google.com](https://console.cloud.google.com/)
2. Enable Speech-to-Text and Translation APIs
3. Download credentials JSON
4. Add to `.env`: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json`

### AssemblyAI (Optional)
1. Sign up at [assemblyai.com](https://www.assemblyai.com/)
2. Get API key
3. Add to `.env`: `ASSEMBLYAI_API_KEY=...`

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Verify database exists: `psql -l`

### Redis Connection Error
- Ensure Redis is running
- Check REDIS_URL in `.env`
- Test connection: `redis-cli ping`

### Celery Worker Not Processing
- Check Redis is running
- Verify CELERY_BROKER_URL in `.env`
- Restart worker

### Out of Memory (Whisper)
- Use smaller model: `WHISPER_MODEL=base` in `.env`
- Or use API instead of local: Install `openai` package

## Next Steps

1. **Read the full documentation**: See [WORKFLOW.md](WORKFLOW.md) for architecture details
2. **Configure API keys**: Add keys for ASR and translation services
3. **Test with real audio**: Upload meeting recordings
4. **Set up Fireflies webhook**: Configure webhook URL in Fireflies dashboard
5. **Deploy to production**: See Docker Compose for production setup

## Support

- **Issues**: Check existing issues or create new one
- **Documentation**: See [WORKFLOW.md](WORKFLOW.md) and [README_API.md](README_API.md)
- **API Docs**: http://localhost:8000/docs

## Quick Reference

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `uv run python run.py` | Start API server |
| `uv run celery -A celery_worker worker --loglevel=info` | Start worker |
| `uv run python init_db.py create` | Initialize database |
| `docker-compose up -d` | Start all services (Docker) |
| `curl http://localhost:8000/health` | Health check |

---

**Ready to go! 🎉** The API server should now be running at http://localhost:8000
