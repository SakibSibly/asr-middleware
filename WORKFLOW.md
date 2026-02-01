# ASR Middleware - Workflow Documentation
## Extending Fireflies.ai for Bengali + English Meetings

### Overview
This middleware system enhances Fireflies.ai by providing robust multi-lingual (Bengali + English) meeting transcription, translation, and storage capabilities.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Meeting Recording Layer                      │
│  - Audio Input (Bn + En mixed or separate speakers)             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audio Processing Pipeline                      │
│  1. Audio capture/upload                                         │
│  2. Speaker diarization (identify who speaks when)               │
│  3. Language detection (segment-level)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              ASR Middleware (This System)                         │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  Bengali ASR      │         │  English ASR      │             │
│  │  - Whisper Large  │         │  - Fireflies.ai   │             │
│  │  - Google Speech  │         │  - Whisper        │             │
│  │  - Assembly AI    │         │  - Assembly AI    │             │
│  └────────┬──────────┘         └────────┬──────────┘             │
│           │                             │                        │
│           └────────────┬────────────────┘                        │
│                        ▼                                         │
│              ┌──────────────────┐                                │
│              │ Text Consolidator │                                │
│              └────────┬──────────┘                                │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Translation Layer                              │
│  - Detect Bengali segments                                       │
│  - Translate Bn → En using:                                      │
│    • Google Translate API                                        │
│    • DeepL API (better quality)                                  │
│    • OpenAI GPT-4 (context-aware)                                │
│    • IndicTrans2 (specialized Indic languages)                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                                │
│  - Original transcripts (Bn + En)                                │
│  - Translated transcripts (all in En)                            │
│  - Metadata (speakers, timestamps, confidence scores)            │
│  - Audio files (optional)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Workflow

### Phase 1: Audio Acquisition
**Input Sources:**
- Live meeting recordings (Zoom, Google Meet, Teams integration)
- Pre-recorded audio/video files
- Real-time audio streams
- Fireflies.ai bot recordings

**Implementation:**
```python
# Meeting can be captured through:
1. Webhook from Fireflies.ai (get audio after meeting)
2. Direct recording via browser/desktop app
3. API integration with meeting platforms
4. Upload interface for offline files
```

### Phase 2: Pre-processing
**Steps:**
1. **Audio Enhancement**
   - Noise reduction
   - Volume normalization
   - Echo cancellation

2. **Speaker Diarization**
   - Identify distinct speakers
   - Create speaker timeline
   - Tools: pyannote.audio, AssemblyAI

3. **Language Detection**
   - Segment-level language identification
   - Detect code-switching (Bn ↔ En)
   - Tools: langdetect, fastText

### Phase 3: Transcription

#### For Bengali Segments:
**Recommended ASR Services (ordered by quality):**

1. **OpenAI Whisper Large-v3** (Best for Bengali)
   - Open-source, high accuracy
   - Supports code-switching
   - Can run locally or via API
   ```python
   import whisper
   model = whisper.load_model("large-v3")
   result = model.transcribe("audio.mp3", language="bn")
   ```

2. **Google Cloud Speech-to-Text**
   - Excellent Bengali support
   - Real-time and batch processing
   - Multiple Bengali models (BN-BD, BN-IN)

3. **AssemblyAI** (New Bengali support)
   - Good accuracy
   - Speaker diarization included
   - Webhook-based processing

4. **Azure Speech Services**
   - Good Bengali recognition
   - Custom model training available

#### For English Segments:
**Recommended Services:**
1. **Fireflies.ai** (Your existing integration)
2. **OpenAI Whisper** (Backup/verification)
3. **AssemblyAI** (Additional features)

### Phase 4: Translation

**Bengali → English Translation Services:**

1. **IndicTrans2** (Recommended for Bengali)
   - Specialized for Indian languages
   - State-of-the-art for Bn→En
   - Open-source, can be self-hosted
   ```bash
   # IndicTrans2 setup
   pip install indictrans2
   ```

2. **OpenAI GPT-4 / GPT-3.5-turbo**
   - Context-aware translation
   - Handles domain-specific terms
   - Can preserve speaker intent
   ```python
   # Example prompt
   "Translate the following Bengali text to English, 
    preserving technical terms and meeting context: [text]"
   ```

3. **Google Cloud Translation API**
   - Fast and reliable
   - Good for general content
   - Cost-effective at scale

4. **DeepL API**
   - High quality translation
   - Natural-sounding English output
   - Limited language pairs (check Bn support)

**Translation Strategy:**
- Use IndicTrans2 for primary translation
- Use GPT-4 for quality checking and refinement
- Preserve timestamps and speaker information
- Handle code-switching intelligently

### Phase 5: Post-processing

**Quality Assurance:**
1. Confidence scoring for each segment
2. Flag low-confidence translations for review
3. Cross-reference with context
4. Spelling and grammar correction

**Formatting:**
1. Paragraph structuring
2. Punctuation restoration
3. Speaker labeling
4. Timestamp alignment

### Phase 6: Storage

**Database Schema:**
```
Meeting
├── id (UUID)
├── title
├── date_time
├── duration
├── participants []
├── audio_file_url
├── status (processing/completed/failed)
└── metadata (meeting platform, quality metrics)

Transcript
├── id (UUID)
├── meeting_id (FK)
├── language (bn/en)
├── text (full transcript)
├── created_at
└── processed_by (service used)

TranscriptSegment
├── id (UUID)
├── transcript_id (FK)
├── speaker_id
├── start_time
├── end_time
├── original_text (Bn or En)
├── translated_text (En) [NULL if already English]
├── original_language
├── confidence_score
├── translation_service (if applicable)
└── metadata (detected language, speaker confidence)

Translation
├── id (UUID)
├── segment_id (FK)
├── source_language
├── target_language
├── source_text
├── translated_text
├── translation_service
├── confidence_score
└── created_at
```

---

## API Endpoints Design

### 1. Meeting Management
```
POST   /api/meetings/                    # Create meeting record
GET    /api/meetings/                    # List meetings
GET    /api/meetings/{id}/               # Get meeting details
DELETE /api/meetings/{id}/               # Delete meeting
```

### 2. Audio Upload/Processing
```
POST   /api/meetings/{id}/upload-audio/  # Upload audio file
POST   /api/meetings/{id}/process/       # Trigger processing
GET    /api/meetings/{id}/status/        # Get processing status
```

### 3. Transcription
```
GET    /api/meetings/{id}/transcript/    # Get full transcript
GET    /api/meetings/{id}/segments/      # Get segmented transcript
POST   /api/meetings/{id}/retranscribe/  # Retry transcription
```

### 4. Translation
```
GET    /api/meetings/{id}/translated/    # Get translated version
POST   /api/segments/{id}/retranslate/   # Retry translation
GET    /api/segments/{id}/original/      # Get original text
```

### 5. Fireflies.ai Integration
```
POST   /api/webhooks/fireflies/          # Webhook endpoint
POST   /api/fireflies/sync/              # Manual sync
GET    /api/fireflies/meetings/          # List Fireflies meetings
```

### 6. Export
```
GET    /api/meetings/{id}/export/txt/    # Export as TXT
GET    /api/meetings/{id}/export/srt/    # Export as SRT (subtitles)
GET    /api/meetings/{id}/export/json/   # Export as JSON
GET    /api/meetings/{id}/export/docx/   # Export as Word doc
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Django models for meetings, transcripts, segments
- [ ] Create database migrations
- [ ] Build basic API endpoints (CRUD for meetings)
- [ ] Set up file storage (S3/local)
- [ ] Configure Celery for async tasks

### Phase 2: Fireflies Integration (Week 2-3)
- [ ] Set up Fireflies.ai API credentials
- [ ] Implement webhook receiver
- [ ] Create Fireflies meeting sync service
- [ ] Download and store audio from Fireflies

### Phase 3: Transcription Pipeline (Week 3-5)
- [ ] Integrate Whisper for Bengali ASR
- [ ] Set up Google Speech-to-Text (backup)
- [ ] Implement language detection
- [ ] Add speaker diarization
- [ ] Create transcription task queue

### Phase 4: Translation Pipeline (Week 5-6)
- [ ] Integrate IndicTrans2 for Bn→En
- [ ] Set up OpenAI GPT API for quality check
- [ ] Implement translation task queue
- [ ] Add confidence scoring
- [ ] Create fallback translation services

### Phase 5: Storage & Retrieval (Week 6-7)
- [ ] Implement transcript storage
- [ ] Create search functionality
- [ ] Build export features (TXT, SRT, JSON, DOCX)
- [ ] Add caching layer (Redis)

### Phase 6: UI & Monitoring (Week 7-8)
- [ ] Build admin dashboard
- [ ] Create meeting viewer interface
- [ ] Add processing status monitor
- [ ] Implement error alerting
- [ ] Create usage analytics

---

## Technology Stack

### Core Framework
- **Django 5.2+** - Web framework
- **Django REST Framework** - API building
- **Celery** - Async task processing
- **Redis** - Task queue & caching
- **PostgreSQL** - Primary database

### ASR & NLP Services
- **OpenAI Whisper** - Primary Bengali ASR
- **Google Cloud Speech-to-Text** - Backup ASR
- **AssemblyAI** - Alternative ASR with diarization
- **Fireflies.ai API** - English transcription & integration

### Translation Services
- **IndicTrans2** - Primary Bn→En translation
- **OpenAI GPT-4** - Context-aware translation & QA
- **Google Translate API** - Backup translation

### Audio Processing
- **pydub** - Audio manipulation
- **librosa** - Audio analysis
- **pyannote.audio** - Speaker diarization
- **noisereduce** - Audio enhancement

### Storage
- **AWS S3 / MinIO** - Audio file storage
- **PostgreSQL** - Structured data
- **Redis** - Caching & sessions

### Monitoring & Logging
- **Sentry** - Error tracking
- **Prometheus + Grafana** - Metrics
- **ELK Stack** - Log aggregation

---

## Environment Variables Required

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1

# Fireflies.ai
FIREFLIES_API_KEY=your-fireflies-key
FIREFLIES_WEBHOOK_SECRET=your-webhook-secret

# OpenAI (for Whisper API & Translation)
OPENAI_API_KEY=your-openai-key

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id

# AssemblyAI
ASSEMBLYAI_API_KEY=your-assemblyai-key

# Translation Services
GOOGLE_TRANSLATE_API_KEY=your-key
DEEPL_API_KEY=your-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

---

## Cost Estimates (Monthly, 100 meetings @ 1hr each)

### ASR Costs
- **Whisper** (Self-hosted): $50-100 (GPU compute)
- **Whisper** (OpenAI API): ~$60 (100 hours @ $0.006/min)
- **Google Speech-to-Text**: ~$144 (100 hours @ $0.024/min)
- **AssemblyAI**: ~$150 (100 hours @ $0.025/min)

### Translation Costs
- **IndicTrans2** (Self-hosted): $20-40 (compute)
- **Google Translate**: ~$20 (1M chars @ $20/1M)
- **OpenAI GPT-4**: ~$100-200 (for QA checks)

### Infrastructure
- **AWS/Cloud hosting**: $100-300
- **Database (RDS)**: $50-100
- **Storage (S3)**: $20-50
- **Redis**: $20-40

**Total Estimated: $500-1,200/month**

---

## Security Considerations

1. **Data Privacy**
   - Encrypt audio files at rest (AES-256)
   - Use TLS for all API communications
   - Implement GDPR-compliant data retention
   - Add meeting data anonymization options

2. **Access Control**
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Per-meeting access permissions
   - API rate limiting

3. **API Security**
   - Webhook signature verification
   - API key rotation policy
   - Input sanitization
   - SQL injection prevention

4. **Compliance**
   - Meeting recording consent
   - Data retention policies
   - Right to deletion (GDPR)
   - Audit logging

---

## Performance Optimization

1. **Async Processing**
   - Use Celery for all heavy tasks
   - Implement task priorities
   - Add retry mechanisms
   - Monitor queue health

2. **Caching Strategy**
   - Cache transcripts (Redis, 24hr TTL)
   - Cache translations (Redis, 7day TTL)
   - Use CDN for audio files
   - Implement API response caching

3. **Database Optimization**
   - Index frequently queried fields
   - Use database connection pooling
   - Implement read replicas
   - Archive old meetings

4. **Scaling Strategy**
   - Horizontal scaling (multiple workers)
   - Load balancing
   - Separate ASR/translation workers
   - Use message queues (RabbitMQ/Redis)

---

## Testing Strategy

1. **Unit Tests**
   - Test each service independently
   - Mock external API calls
   - Test error handling

2. **Integration Tests**
   - Test full pipeline (audio → transcript → translation)
   - Test Fireflies webhook
   - Test API endpoints

3. **Quality Tests**
   - Benchmark ASR accuracy (WER - Word Error Rate)
   - Measure translation quality (BLEU score)
   - Test with real meeting recordings

4. **Performance Tests**
   - Load testing (concurrent meetings)
   - Stress testing (large audio files)
   - API response time monitoring

---

## Monitoring & Alerting

**Key Metrics to Track:**
- Processing time per meeting
- ASR accuracy (confidence scores)
- Translation quality scores
- API error rates
- Queue depth and processing lag
- Storage usage
- Cost per meeting

**Alerts:**
- Failed transcription/translation
- High error rates (>5%)
- Queue backup (>30 min delay)
- API quota approaching limit
- Storage approaching capacity

---

## Future Enhancements

1. **Advanced Features**
   - Real-time transcription (live meetings)
   - Automatic meeting summarization
   - Action item extraction
   - Sentiment analysis
   - Key topic identification

2. **Multi-language Support**
   - Add Hindi support
   - Add other Indic languages
   - Support more language pairs

3. **Integration Expansions**
   - Slack notifications
   - Calendar integration
   - CRM integration (Salesforce, HubSpot)
   - Team collaboration tools

4. **AI Enhancements**
   - Custom vocabulary training
   - Domain-specific models
   - Speaker recognition (voice biometrics)
   - Automatic punctuation and formatting

---

## Quick Start Commands

```bash
# 1. Clone and setup
cd asr-middleware
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 4. Database setup
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start services
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A core worker -l info

# Terminal 3: Celery beat (scheduled tasks)
celery -A core beat -l info

# 7. Test webhook endpoint
curl -X POST http://localhost:8000/api/webhooks/fireflies/ \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'
```

---

## Support & Maintenance

**Regular Tasks:**
- Monitor API quotas daily
- Review failed transcriptions weekly
- Update ASR models monthly
- Backup database daily
- Review and optimize costs monthly

**Documentation:**
- Keep API documentation updated
- Document configuration changes
- Maintain runbook for common issues
- Update this workflow as system evolves

---

## Contact & Resources

**Useful Links:**
- Fireflies.ai API: https://docs.fireflies.ai/
- Whisper: https://github.com/openai/whisper
- IndicTrans2: https://github.com/AI4Bharat/IndicTrans2
- Google Speech-to-Text: https://cloud.google.com/speech-to-text/docs
- AssemblyAI: https://www.assemblyai.com/docs

---

*Last Updated: February 1, 2026*
