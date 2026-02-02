"""
Fireflies.ai API integration service
"""

import requests
from typing import List, Dict, Optional

from app.config import settings


class FirefliesService:
    """Fireflies.ai API client"""
    
    def __init__(self):
        self.api_url = settings.FIREFLIES_API_URL
        self.api_key = settings.FIREFLIES_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def get_recent_meetings(self, limit: int = 10) -> List[Dict]:
        """
        Fetch recent meetings from Fireflies.ai
        
        Args:
            limit: Number of meetings to fetch
            
        Returns:
            List of meeting dictionaries
        """
        query = """
        query GetTranscripts($limit: Int!) {
          transcripts(limit: $limit) {
            id
            title
            date
            duration
            audio_url
            transcript_url
            participants
            summary
          }
        }
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "query": query,
                    "variables": {"limit": limit},
                },
                timeout=30,
            )
            response.raise_for_status()
            
            data = response.json()
            transcripts = data.get("data", {}).get("transcripts", [])
            
            # Format meetings
            meetings = []
            for transcript in transcripts:
                meetings.append({
                    "id": transcript["id"],
                    "title": transcript.get("title", "Untitled Meeting"),
                    "date": transcript.get("date"),
                    "duration": transcript.get("duration"),
                    "audio_url": transcript.get("audio_url"),
                    "transcript_url": transcript.get("transcript_url"),
                    "participants": transcript.get("participants", []),
                    "metadata": {
                        "summary": transcript.get("summary"),
                    },
                })
            
            return meetings
        
        except Exception as e:
            raise Exception(f"Failed to fetch Fireflies meetings: {str(e)}")
    
    async def get_meeting_details(self, meeting_id: str) -> Dict:
        """
        Get detailed information about a specific meeting
        
        Args:
            meeting_id: Fireflies meeting ID
            
        Returns:
            Meeting details dictionary
        """
        query = """
        query GetTranscript($transcriptId: String!) {
          transcript(id: $transcriptId) {
            id
            title
            date
            duration
            audio_url
            transcript_url
            participants
            sentences {
              text
              start_time
              end_time
              speaker_name
            }
            summary
            action_items
            keywords
          }
        }
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "query": query,
                    "variables": {"transcriptId": meeting_id},
                },
                timeout=30,
            )
            response.raise_for_status()
            
            data = response.json()
            transcript = data.get("data", {}).get("transcript", {})
            
            return transcript
        
        except Exception as e:
            raise Exception(f"Failed to fetch meeting details: {str(e)}")
    
    async def download_audio(self, audio_url: str, save_path: str) -> str:
        """
        Download audio file from Fireflies
        
        Args:
            audio_url: URL to audio file
            save_path: Local path to save audio
            
        Returns:
            Path to saved file
        """
        try:
            response = requests.get(audio_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return save_path
        
        except Exception as e:
            raise Exception(f"Failed to download audio: {str(e)}")
