# ASR Middleware - API Documentation

Base URL: `http://localhost:8000/api/`

## Authentication

All endpoints except webhooks require JWT authentication:

```bash
# Get access token
POST /api/token/
{
  "username": "your_username",
  "password": "your_password"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use in requests
Authorization: Bearer <access_token>
```

---

## Meetings API

### 1. List Meetings

```http
GET /api/meetings/
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, processing, completed, failed)
- `date_from` (optional): Filter by date (YYYY-MM-DD)
- `date_to` (optional): Filter by date (YYYY-MM-DD)
- `search` (optional): Search in title
- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 20)

**Response:**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/meetings/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Team Standup - Feb 1",
      "date_time": "2026-02-01T10:00:00Z",
      "duration": 1800,
      "participant_count": 5,
      "status": "completed",
      "created_at": "2026-02-01T09:00:00Z",
      "updated_at": "2026-02-01T10:35:00Z"
    }
  ]
}
```

### 2. Create Meeting

```http
POST /api/meetings/
```

**Request Body:**
```json
{
  "title": "Product Review Meeting",
  "date_time": "2026-02-01T14:00:00Z",
  "duration": 3600,
  "participants": ["Alice", "Bob", "Charlie"],
  "audio_url": "https://example.com/audio.mp3",
  "metadata": {
    "platform": "zoom",
    "meeting_id": "123456789"
  }
}
```

**Response:** (201 Created)
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "Product Review Meeting",
  "date_time": "2026-02-01T14:00:00Z",
  "duration": 3600,
  "participants": ["Alice", "Bob", "Charlie"],
  "audio_file": null,
  "audio_url": "https://example.com/audio.mp3",
  "status": "pending",
  "fireflies_id": null,
  "metadata": {
    "platform": "zoom",
    "meeting_id": "123456789"
  },
  "created_at": "2026-02-01T13:00:00Z",
  "updated_at": "2026-02-01T13:00:00Z",
  "transcripts": [],
  "jobs": []
}
```

### 3. Get Meeting Details

```http
GET /api/meetings/{meeting_id}/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Team Standup",
  "date_time": "2026-02-01T10:00:00Z",
  "duration": 1800,
  "participants": ["Alice", "Bob"],
  "audio_file": "/media/meetings/2026/02/audio_abc123.mp3",
  "audio_file_url": "http://localhost:8000/media/meetings/2026/02/audio_abc123.mp3",
  "audio_url": null,
  "status": "completed",
  "fireflies_id": null,
  "metadata": {},
  "created_at": "2026-02-01T09:00:00Z",
  "updated_at": "2026-02-01T10:35:00Z",
  "transcripts": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "meeting": "550e8400-e29b-41d4-a716-446655440000",
      "language": "bn",
      "text": "আজকের মিটিংয়ে আমরা প্রোজেক্টের অগ্রগতি নিয়ে আলোচনা করব...",
      "processed_by": "whisper-large-v3",
      "processing_time": 45.2,
      "created_at": "2026-02-01T10:15:00Z",
      "segment_count": 24
    }
  ],
  "jobs": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "meeting": "550e8400-e29b-41d4-a716-446655440000",
      "job_type": "transcription",
      "status": "completed",
      "started_at": "2026-02-01T10:10:00Z",
      "completed_at": "2026-02-01T10:15:00Z",
      "duration": 300.0,
      "error_message": null,
      "metadata": {},
      "created_at": "2026-02-01T10:10:00Z"
    }
  ]
}
```

### 4. Upload Audio File

```http
POST /api/meetings/{meeting_id}/upload-audio/
Content-Type: multipart/form-data
```

**Request Body:**
```
audio_file: <binary file data>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "message": "Audio file uploaded successfully",
  "audio_file_url": "http://localhost:8000/media/meetings/2026/02/audio_xyz789.mp3"
}
```

### 5. Process Meeting

```http
POST /api/meetings/{meeting_id}/process/
```

**Request Body:** (optional)
```json
{
  "language": "auto",  // or "bn", "en"
  "enable_translation": true,
  "translation_method": "auto"  // or "google", "gpt"
}
```

**Response:** (202 Accepted)
```json
{
  "success": true,
  "message": "Processing started",
  "job_id": "990e8400-e29b-41d4-a716-446655440004",
  "celery_task_id": "1234-5678-90ab-cdef"
}
```

### 6. Get Processing Status

```http
GET /api/meetings/{meeting_id}/status/
```

**Response:**
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "jobs": [
    {
      "job_type": "transcription",
      "status": "processing",
      "progress": 65,
      "started_at": "2026-02-01T10:10:00Z"
    },
    {
      "job_type": "translation",
      "status": "pending",
      "progress": 0,
      "started_at": null
    }
  ],
  "estimated_completion": "2026-02-01T10:25:00Z"
}
```

### 7. Delete Meeting

```http
DELETE /api/meetings/{meeting_id}/
```

**Response:** (204 No Content)

---

## Transcripts API

### 1. Get Full Transcript

```http
GET /api/meetings/{meeting_id}/transcript/
```

**Query Parameters:**
- `language` (optional): Filter by language (bn, en, mixed)
- `format` (optional): Response format (json, txt, srt, vtt)

**Response (JSON):**
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "meeting_title": "Team Standup",
  "language": "bn",
  "text": "আজকের মিটিংয়ে আমরা প্রোজেক্টের অগ্রগতি নিয়ে আলোচনা করব...",
  "processed_by": "whisper-large-v3",
  "segment_count": 24,
  "created_at": "2026-02-01T10:15:00Z"
}
```

**Response (TXT format):**
```
Team Standup
Date: 2026-02-01 10:00:00 UTC
Duration: 30 minutes
Language: Bengali (bn)
Processed by: whisper-large-v3

---

আজকের মিটিংয়ে আমরা প্রোজেক্টের অগ্রগতি নিয়ে আলোচনা করব...
```

### 2. Get Segmented Transcript

```http
GET /api/meetings/{meeting_id}/segments/
```

**Query Parameters:**
- `language` (optional): Filter by language
- `speaker` (optional): Filter by speaker ID
- `start_time` (optional): Filter segments after this time (seconds)
- `end_time` (optional): Filter segments before this time (seconds)
- `with_translation` (optional): Include translated text (true/false)

**Response:**
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "segment_count": 24,
  "segments": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "speaker_id": "SPEAKER_00",
      "speaker_name": "Alice",
      "start_time": 0.0,
      "end_time": 5.2,
      "duration": 5.2,
      "original_text": "আজকের মিটিংয়ে শুরু করছি",
      "original_language": "bn",
      "translated_text": "Starting today's meeting",
      "translation_service": "google-translate",
      "confidence_score": 0.95,
      "translation_confidence": 0.92,
      "metadata": {}
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "speaker_id": "SPEAKER_01",
      "speaker_name": "Bob",
      "start_time": 5.5,
      "end_time": 12.3,
      "duration": 6.8,
      "original_text": "ধন্যবাদ। আমি প্রথমে রিপোর্ট করছি",
      "original_language": "bn",
      "translated_text": "Thank you. I'll report first",
      "translation_service": "google-translate",
      "confidence_score": 0.93,
      "translation_confidence": 0.89,
      "metadata": {}
    }
  ]
}
```

### 3. Get Translated Transcript

```http
GET /api/meetings/{meeting_id}/translated/
```

**Query Parameters:**
- `format` (optional): Response format (json, txt, srt, vtt)

**Response:**
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "meeting_title": "Team Standup",
  "original_language": "bn",
  "target_language": "en",
  "segment_count": 24,
  "segments": [
    {
      "speaker": "Alice",
      "start_time": 0.0,
      "end_time": 5.2,
      "original_text": "আজকের মিটিংয়ে শুরু করছি",
      "translated_text": "Starting today's meeting"
    }
  ],
  "full_translated_text": "Starting today's meeting. Thank you. I'll report first..."
}
```

### 4. Retranscribe Meeting

```http
POST /api/meetings/{meeting_id}/retranscribe/
```

**Request Body:**
```json
{
  "service": "whisper",  // or "google", "assemblyai"
  "language": "bn",
  "force": true
}
```

**Response:** (202 Accepted)
```json
{
  "success": true,
  "message": "Retranscription job created",
  "job_id": "cc0e8400-e29b-41d4-a716-446655440007"
}
```

---

## Segments API

### 1. Get Segment Details

```http
GET /api/segments/{segment_id}/
```

**Response:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "transcript": "770e8400-e29b-41d4-a716-446655440002",
  "speaker_id": "SPEAKER_00",
  "speaker_name": "Alice",
  "start_time": 0.0,
  "end_time": 5.2,
  "duration": 5.2,
  "original_text": "আজকের মিটিংয়ে শুরু করছি",
  "original_language": "bn",
  "translated_text": "Starting today's meeting",
  "translation_service": "google-translate",
  "confidence_score": 0.95,
  "translation_confidence": 0.92,
  "metadata": {},
  "created_at": "2026-02-01T10:15:00Z"
}
```

### 2. Retranslate Segment

```http
POST /api/segments/{segment_id}/retranslate/
```

**Request Body:**
```json
{
  "service": "gpt",  // or "google", "auto"
  "context": "This is a technical meeting about software development"
}
```

**Response:**
```json
{
  "success": true,
  "segment_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "original_text": "আজকের মিটিংয়ে শুরু করছি",
  "translated_text": "Starting today's meeting",
  "previous_translation": "I am starting in today's meeting",
  "service": "openai-gpt4",
  "confidence": 0.97
}
```

### 3. Get Original Text

```http
GET /api/segments/{segment_id}/original/
```

**Response:**
```json
{
  "segment_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "original_text": "আজকের মিটিংয়ে শুরু করছি",
  "language": "bn",
  "confidence_score": 0.95
}
```

---

## Export API

### 1. Export as Text

```http
GET /api/meetings/{meeting_id}/export/txt/
```

**Query Parameters:**
- `include_translation` (optional): Include translated text (true/false)
- `include_timestamps` (optional): Include timestamps (true/false)
- `include_speakers` (optional): Include speaker names (true/false)

**Response:** (text/plain)
```
Team Standup
2026-02-01 10:00:00 UTC
Duration: 30 minutes

---

[00:00:00] Alice: আজকের মিটিংয়ে শুরু করছি
           [EN: Starting today's meeting]

[00:00:05] Bob: ধন্যবাদ। আমি প্রথমে রিপোর্ট করছি
         [EN: Thank you. I'll report first]
```

### 2. Export as SRT Subtitles

```http
GET /api/meetings/{meeting_id}/export/srt/
```

**Query Parameters:**
- `language` (optional): Language to export (original/translated)

**Response:** (application/x-subrip)
```srt
1
00:00:00,000 --> 00:00:05,200
আজকের মিটিংয়ে শুরু করছি

2
00:00:05,500 --> 00:00:12,300
ধন্যবাদ। আমি প্রথমে রিপোর্ট করছি
```

### 3. Export as JSON

```http
GET /api/meetings/{meeting_id}/export/json/
```

**Response:** (application/json)
```json
{
  "meeting": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Team Standup",
    "date_time": "2026-02-01T10:00:00Z",
    "duration": 1800,
    "participants": ["Alice", "Bob"]
  },
  "transcripts": [
    {
      "language": "bn",
      "segments": [
        {
          "speaker": "Alice",
          "start": 0.0,
          "end": 5.2,
          "text": "আজকের মিটিংয়ে শুরু করছি",
          "translation": "Starting today's meeting"
        }
      ]
    }
  ]
}
```

### 4. Export as Word Document

```http
GET /api/meetings/{meeting_id}/export/docx/
```

**Query Parameters:**
- `include_translation` (optional): Include translated text (true/false)
- `format_style` (optional): Document style (simple/detailed/professional)

**Response:** (application/vnd.openxmlformats-officedocument.wordprocessingml.document)

---

## Fireflies Integration API

### 1. Webhook Endpoint

```http
POST /api/webhooks/fireflies/
X-Fireflies-Signature: <signature>
```

**Request Body:**
```json
{
  "event": "transcription_ready",
  "meeting_id": "fireflies_123456",
  "title": "Team Standup",
  "date": "2026-02-01T10:00:00Z",
  "duration": 1800,
  "audio_url": "https://fireflies.ai/audio/abc123.mp3",
  "transcript_url": "https://fireflies.ai/transcript/abc123.json",
  "participants": ["alice@example.com", "bob@example.com"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook received and processing started",
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Manual Sync

```http
POST /api/fireflies/sync/
```

**Request Body:**
```json
{
  "fireflies_meeting_id": "fireflies_123456"
}
```

**Response:**
```json
{
  "success": true,
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

### 3. List Fireflies Meetings

```http
GET /api/fireflies/meetings/
```

**Query Parameters:**
- `date_from` (optional): Filter by date
- `date_to` (optional): Filter by date
- `synced` (optional): Filter by sync status (true/false)

**Response:**
```json
{
  "count": 10,
  "meetings": [
    {
      "fireflies_id": "fireflies_123456",
      "title": "Team Standup",
      "date": "2026-02-01T10:00:00Z",
      "synced": true,
      "local_meeting_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request data",
  "details": {
    "audio_file": ["This field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Meeting not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "abc123"
}
```

---

## Rate Limits

- **Authenticated requests**: 1000 requests/hour
- **Webhook endpoints**: 100 requests/minute
- **Upload endpoints**: 50 requests/hour

Rate limit headers included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1738416000
```

---

## Webhooks

### Event Types

1. **meeting.created**: New meeting created
2. **meeting.processing**: Processing started
3. **meeting.completed**: Processing completed
4. **meeting.failed**: Processing failed
5. **transcript.created**: New transcript created
6. **translation.completed**: Translation completed

### Webhook Payload Example

```json
{
  "event": "meeting.completed",
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-01T10:35:00Z",
  "data": {
    "title": "Team Standup",
    "status": "completed",
    "transcript_id": "770e8400-e29b-41d4-a716-446655440002",
    "processing_time": 300.0
  }
}
```

---

## SDK Examples

### Python

```python
import requests

class ASRMiddlewareClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_meeting(self, title, date_time, audio_file_path):
        # Create meeting
        response = requests.post(
            f'{self.base_url}/meetings/',
            headers=self.headers,
            json={
                'title': title,
                'date_time': date_time
            }
        )
        meeting = response.json()
        
        # Upload audio
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': f}
            requests.post(
                f'{self.base_url}/meetings/{meeting["id"]}/upload-audio/',
                headers={'Authorization': self.headers['Authorization']},
                files=files
            )
        
        # Start processing
        requests.post(
            f'{self.base_url}/meetings/{meeting["id"]}/process/',
            headers=self.headers
        )
        
        return meeting['id']
    
    def get_transcript(self, meeting_id):
        response = requests.get(
            f'{self.base_url}/meetings/{meeting_id}/transcript/',
            headers=self.headers
        )
        return response.json()

# Usage
client = ASRMiddlewareClient('http://localhost:8000/api', 'your-api-key')
meeting_id = client.create_meeting(
    'Team Meeting',
    '2026-02-01T14:00:00Z',
    'meeting_audio.mp3'
)
transcript = client.get_transcript(meeting_id)
print(transcript['text'])
```

### JavaScript

```javascript
class ASRMiddlewareClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  async createMeeting(title, dateTime, audioFile) {
    // Create meeting
    const meetingResponse = await fetch(`${this.baseUrl}/meetings/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ title, date_time: dateTime })
    });
    const meeting = await meetingResponse.json();
    
    // Upload audio
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    await fetch(`${this.baseUrl}/meetings/${meeting.id}/upload-audio/`, {
      method: 'POST',
      headers: {
        'Authorization': this.headers.Authorization
      },
      body: formData
    });
    
    // Start processing
    await fetch(`${this.baseUrl}/meetings/${meeting.id}/process/`, {
      method: 'POST',
      headers: this.headers
    });
    
    return meeting.id;
  }
  
  async getTranscript(meetingId) {
    const response = await fetch(
      `${this.baseUrl}/meetings/${meetingId}/transcript/`,
      { headers: this.headers }
    );
    return response.json();
  }
}

// Usage
const client = new ASRMiddlewareClient('http://localhost:8000/api', 'your-api-key');
const meetingId = await client.createMeeting(
  'Team Meeting',
  '2026-02-01T14:00:00Z',
  audioFileBlob
);
const transcript = await client.getTranscript(meetingId);
console.log(transcript.text);
```

---

*API Version: 1.0.0*
*Last Updated: February 1, 2026*
