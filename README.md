# ASR Middleware

An Automatic Speech Recognition (ASR) middleware that extends Fireflies.ai capabilities to provide robust support for Bengali (Bn) + English (En) mixed-language meetings. This system offers high-quality transcription, translation, and storage for multilingual meeting content.

## 🎯 Features

- **Multi-language ASR**: Support for Bengali and English with automatic language detection
- **Fireflies.ai Integration**: Seamless integration with Fireflies.ai for enhanced meeting management
- **High-Quality Transcription**: Uses OpenAI Whisper (Large-v3) for Bengali, with fallback to Google Speech-to-Text
- **Intelligent Translation**: Bengali to English translation using multiple services (IndicTrans2, GPT-4, Google Translate)
- **Speaker Diarization**: Identify and track different speakers throughout the meeting
- **Code-switching Support**: Handle meetings where speakers switch between Bengali and English
- **RESTful API**: Complete API for meeting management, transcription, and translation
- **Async Processing**: Background task processing using Celery for scalable operations
- **Multiple Export Formats**: Export transcripts as TXT, SRT, JSON, DOCX

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Redis 6+
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd asr-middleware
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start the services**

   Terminal 1 - Django Server:
   ```bash
   python manage.py runserver
   ```

   Terminal 2 - Celery Worker:
   ```bash
   celery -A core worker -l info
   ```

   Terminal 3 - Celery Beat (scheduled tasks):
   ```bash
   celery -A core beat -l info
   ```

7. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - API Docs: http://localhost:8000/api/docs/

## 📖 Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete system architecture and workflow documentation
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Technical implementation guide and code examples
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference with examples

## 🏗️ Architecture

```
Meeting Recording → Audio Processing → ASR (Bn/En) → Translation (Bn→En) → Storage
                         ↓
                  Speaker Diarization
                         ↓
                  Language Detection
```

### Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **ASR Services**: OpenAI Whisper, Google Speech-to-Text, AssemblyAI
- **Translation**: IndicTrans2, OpenAI GPT-4, Google Translate
- **Storage**: AWS S3 or local filesystem
- **Audio Processing**: pydub, librosa, pyannote.audio

## 🔧 Configuration

### Essential Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

# ASR Services (at least one)
OPENAI_API_KEY=your-openai-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
ASSEMBLYAI_API_KEY=your-assemblyai-key

# Translation Services
GOOGLE_TRANSLATE_API_KEY=your-google-key

# Optional: Fireflies Integration
FIREFLIES_API_KEY=your-fireflies-key
```

See [.env.example](.env.example) for all configuration options.

## 📝 Usage Example

### Python Client

```python
import requests

# Authenticate
response = requests.post('http://localhost:8000/api/token/', 
    json={'username': 'admin', 'password': 'password'})
token = response.json()['access']
headers = {'Authorization': f'Bearer {token}'}

# Create meeting
meeting = requests.post('http://localhost:8000/api/meetings/',
    headers=headers,
    json={
        'title': 'Team Standup',
        'date_time': '2026-02-01T10:00:00Z'
    }).json()

# Upload audio
with open('meeting.mp3', 'rb') as f:
    requests.post(
        f'http://localhost:8000/api/meetings/{meeting["id"]}/upload-audio/',
        headers=headers,
        files={'audio_file': f}
    )

# Start processing
requests.post(
    f'http://localhost:8000/api/meetings/{meeting["id"]}/process/',
    headers=headers
)

# Get transcript (after processing)
transcript = requests.get(
    f'http://localhost:8000/api/meetings/{meeting["id"]}/transcript/',
    headers=headers
).json()

print(transcript['text'])
```

## 🔄 Workflow

1. **Meeting Recording**: Upload audio file or sync from Fireflies.ai
2. **Pre-processing**: Audio enhancement, noise reduction
3. **Language Detection**: Identify Bengali/English segments
4. **Transcription**: 
   - Bengali segments → Whisper Large-v3
   - English segments → Fireflies.ai or Whisper
5. **Speaker Diarization**: Identify and label speakers
6. **Translation**: Translate Bengali segments to English
7. **Storage**: Save original + translated transcripts
8. **Export**: Available in multiple formats (TXT, SRT, JSON, DOCX)

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test meetings

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoring

- **Celery Flower**: Monitor task queue
  ```bash
  celery -A core flower
  ```
  Access at http://localhost:5555

- **Django Admin**: View meetings, transcripts, jobs
  Access at http://localhost:8000/admin/

## 🔐 Security

- JWT-based authentication
- CORS configuration for frontend integration
- File upload size limits
- API rate limiting
- Webhook signature verification
- Encrypted storage for audio files

## 💰 Cost Estimates

For 100 hours of meetings per month:
- **Whisper (self-hosted)**: ~$50-100 (GPU compute)
- **Google Cloud**: ~$144 (Speech-to-Text) + ~$20 (Translation)
- **OpenAI**: ~$60 (Whisper API) + ~$100-200 (GPT-4 translation)
- **Infrastructure**: ~$200-500 (AWS/Cloud hosting)

**Total**: ~$500-1,200/month

See [WORKFLOW.md](WORKFLOW.md) for detailed cost breakdown.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI Whisper for excellent open-source ASR
- Fireflies.ai for meeting management inspiration
- AI4Bharat for IndicTrans2 Bengali translation models
- Django and Django REST Framework communities

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check [WORKFLOW.md](WORKFLOW.md) for detailed documentation
- Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API usage

---

**Note**: This middleware is designed to extend and enhance Fireflies.ai capabilities specifically for Bengali + English meetings. It can work standalone or integrated with Fireflies.ai.
