"""
Translation service
Integrates multiple translation providers for Bengali to English translation
"""

from typing import Dict, Optional
from enum import Enum

from app.config import settings


class TranslationProvider(str, Enum):
    """Available translation providers"""
    INDICTRANS2 = "indictrans2"
    GOOGLE = "google"
    OPENAI = "openai"
    DEEPL = "deepl"


class TranslationService:
    """Translation service manager"""
    
    def __init__(self):
        self.indictrans_model = None
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str = "en",
        service: Optional[str] = None,
    ) -> Dict:
        """
        Translate text
        
        Args:
            text: Text to translate
            source_lang: Source language code (bn/en)
            target_lang: Target language code (default: en)
            service: Specific service to use (optional)
            
        Returns:
            Dict with translated text and metadata
        """
        # Skip translation if already in target language
        if source_lang == target_lang:
            return {
                "text": text,
                "service": "none",
                "confidence": 1.0,
            }
        
        # Determine which service to use
        if service:
            provider = TranslationProvider(service)
        else:
            # Use IndicTrans2 by default for Bengali
            provider = TranslationProvider.INDICTRANS2 if source_lang == "bn" else TranslationProvider.GOOGLE
        
        if provider == TranslationProvider.INDICTRANS2:
            return await self._translate_indictrans(text, source_lang, target_lang)
        elif provider == TranslationProvider.GOOGLE:
            return await self._translate_google(text, source_lang, target_lang)
        elif provider == TranslationProvider.OPENAI:
            return await self._translate_openai(text, source_lang, target_lang)
        elif provider == TranslationProvider.DEEPL:
            return await self._translate_deepl(text, source_lang, target_lang)
        else:
            raise ValueError(f"Unsupported translation provider: {provider}")
    
    async def _translate_indictrans(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Translate using IndicTrans2"""
        try:
            # Note: IndicTrans2 requires specific setup
            # This is a placeholder implementation
            # Actual implementation would use the IndicTrans2 model
            
            print(f"Translating with IndicTrans2: {source_lang} -> {target_lang}")
            
            # TODO: Implement actual IndicTrans2 translation
            # For now, fallback to Google
            return await self._translate_google(text, source_lang, target_lang)
        
        except Exception as e:
            raise Exception(f"IndicTrans2 translation failed: {str(e)}")
    
    async def _translate_google(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Translate using Google Translate API"""
        try:
            from google.cloud import translate_v2 as translate
            
            client = translate.Client()
            
            # Perform translation
            result = client.translate(
                text,
                source_language=source_lang,
                target_language=target_lang,
            )
            
            return {
                "text": result["translatedText"],
                "service": "google",
                "confidence": 0.9,  # Google doesn't provide confidence scores
                "detected_source_language": result.get("detectedSourceLanguage"),
            }
        
        except Exception as e:
            raise Exception(f"Google translation failed: {str(e)}")
    
    async def _translate_openai(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Translate using OpenAI GPT"""
        try:
            import openai
            
            openai.api_key = settings.OPENAI_API_KEY
            
            lang_names = {
                "bn": "Bengali",
                "en": "English",
            }
            
            prompt = f"""Translate the following {lang_names.get(source_lang, source_lang)} text to {lang_names.get(target_lang, target_lang)}.
Preserve the meaning, tone, and context. Keep technical terms and proper nouns as appropriate.

Text: {text}

Translation:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in Bengali and English."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {
                "text": translated_text,
                "service": "openai",
                "confidence": 0.95,
                "model": "gpt-4",
            }
        
        except Exception as e:
            raise Exception(f"OpenAI translation failed: {str(e)}")
    
    async def _translate_deepl(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Translate using DeepL API"""
        try:
            import deepl
            
            translator = deepl.Translator(settings.DEEPL_API_KEY)
            
            # Map language codes
            deepl_source = source_lang.upper()
            deepl_target = target_lang.upper()
            
            result = translator.translate_text(
                text,
                source_lang=deepl_source,
                target_lang=deepl_target,
            )
            
            return {
                "text": result.text,
                "service": "deepl",
                "confidence": 0.95,
                "detected_source_language": result.detected_source_lang,
            }
        
        except Exception as e:
            raise Exception(f"DeepL translation failed: {str(e)}")
