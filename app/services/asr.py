"""
ASR (Automatic Speech Recognition) service
Integrates multiple ASR providers for Bengali and English transcription
"""

import os
from typing import Dict, List, Optional
from enum import Enum

from app.config import settings


class ASRProvider(str, Enum):
    """Available ASR providers"""
    WHISPER = "whisper"
    GOOGLE = "google"
    ASSEMBLYAI = "assemblyai"
    FIREFLIES = "fireflies"


class ASRService:
    """ASR service manager"""
    
    def __init__(self):
        self.whisper_model = None
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        provider: ASRProvider = ASRProvider.WHISPER,
        enable_diarization: bool = True,
    ) -> Dict:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            language: Language code (bn/en) or None for auto-detect
            provider: ASR provider to use
            enable_diarization: Enable speaker diarization
            
        Returns:
            Dict with transcription results including segments
        """
        if provider == ASRProvider.WHISPER:
            return await self._transcribe_whisper(audio_path, language)
        elif provider == ASRProvider.GOOGLE:
            return await self._transcribe_google(audio_path, language)
        elif provider == ASRProvider.ASSEMBLYAI:
            return await self._transcribe_assemblyai(audio_path, enable_diarization)
        else:
            raise ValueError(f"Unsupported ASR provider: {provider}")
    
    async def _transcribe_whisper(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict:
        """Transcribe using OpenAI Whisper"""
        try:
            import whisper
            
            # Load model (cached after first load)
            if self.whisper_model is None:
                model_name = settings.WHISPER_MODEL
                print(f"Loading Whisper model: {model_name}")
                self.whisper_model = whisper.load_model(model_name)
            
            # Transcribe
            print(f"Transcribing with Whisper: {audio_path}")
            result = self.whisper_model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                word_timestamps=True,
            )
            
            # Format segments
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start_time": segment["start"],
                    "end_time": segment["end"],
                    "text": segment["text"].strip(),
                    "confidence": segment.get("confidence", 0.0),
                    "language": result.get("language", language or "unknown"),
                })
            
            return {
                "text": result["text"],
                "language": result.get("language", language or "unknown"),
                "segments": segments,
                "provider": "whisper",
                "confidence": sum(s.get("confidence", 0) for s in segments) / len(segments) if segments else 0.0,
            }
        
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")
    
    async def _transcribe_google(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict:
        """Transcribe using Google Cloud Speech-to-Text"""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Configure recognition
            lang_code = "bn-BD" if language == "bn" else "en-US"
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code=lang_code,
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
            )
            
            # Perform transcription
            response = client.recognize(config=config, audio=audio)
            
            # Format results
            segments = []
            full_text = ""
            
            for result in response.results:
                alternative = result.alternatives[0]
                full_text += alternative.transcript + " "
                
                if result.result_end_time:
                    segments.append({
                        "start_time": 0,  # Google doesn't provide start time easily
                        "end_time": result.result_end_time.total_seconds(),
                        "text": alternative.transcript,
                        "confidence": alternative.confidence,
                        "language": language or "unknown",
                    })
            
            return {
                "text": full_text.strip(),
                "language": language or "unknown",
                "segments": segments,
                "provider": "google",
                "confidence": sum(s["confidence"] for s in segments) / len(segments) if segments else 0.0,
            }
        
        except Exception as e:
            raise Exception(f"Google transcription failed: {str(e)}")
    
    async def _transcribe_assemblyai(
        self,
        audio_path: str,
        enable_diarization: bool = True,
    ) -> Dict:
        """Transcribe using AssemblyAI"""
        try:
            import assemblyai as aai
            
            aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
            
            config = aai.TranscriptionConfig(
                speaker_labels=enable_diarization,
                language_detection=True,
            )
            
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"AssemblyAI error: {transcript.error}")
            
            # Format segments
            segments = []
            for utterance in transcript.utterances or []:
                segments.append({
                    "start_time": utterance.start / 1000.0,  # Convert ms to seconds
                    "end_time": utterance.end / 1000.0,
                    "text": utterance.text,
                    "confidence": utterance.confidence,
                    "speaker_id": f"speaker_{utterance.speaker}" if enable_diarization else None,
                    "language": transcript.language_code or "unknown",
                })
            
            return {
                "text": transcript.text,
                "language": transcript.language_code or "unknown",
                "segments": segments,
                "provider": "assemblyai",
                "confidence": transcript.confidence,
            }
        
        except Exception as e:
            raise Exception(f"AssemblyAI transcription failed: {str(e)}")
    
    def detect_language(self, audio_path: str) -> str:
        """Detect language of audio file"""
        try:
            import whisper
            
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")
            
            # Load audio and detect language
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)
            _, probs = self.whisper_model.detect_language(mel)
            
            detected_lang = max(probs, key=probs.get)
            return detected_lang
        
        except Exception as e:
            print(f"Language detection failed: {str(e)}")
            return "unknown"
