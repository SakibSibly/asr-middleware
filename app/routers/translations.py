"""
Translation management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.schemas import TranslationRequest, TranslationResponse
from app.models import TranscriptSegment, Translation
from app.services.translation import TranslationService

router = APIRouter()
translation_service = TranslationService()


@router.post("/translate", response_model=TranslationResponse)
async def translate_segment(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Translate a transcript segment"""
    segment = db.query(TranscriptSegment).filter(
        TranscriptSegment.id == request.segment_id
    ).first()
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )
    
    # Perform translation
    translated_text = await translation_service.translate(
        text=segment.original_text,
        source_lang=segment.original_language,
        target_lang=request.target_language,
        service=request.service,
    )
    
    # Save translation
    translation = Translation(
        segment_id=segment.id,
        source_language=segment.original_language,
        target_language=request.target_language,
        source_text=segment.original_text,
        translated_text=translated_text["text"],
        translation_service=translated_text["service"],
        confidence_score=translated_text.get("confidence"),
        is_active=True,
    )
    
    # Mark previous translations as inactive
    db.query(Translation).filter(
        Translation.segment_id == segment.id,
        Translation.target_language == request.target_language,
    ).update({"is_active": False})
    
    db.add(translation)
    
    # Update segment with translated text
    segment.translated_text = translated_text["text"]
    segment.translation_service = translated_text["service"]
    
    db.commit()
    db.refresh(translation)
    
    return translation


@router.get("/segment/{segment_id}/history", response_model=List[TranslationResponse])
async def get_translation_history(
    segment_id: str,
    db: Session = Depends(get_db),
):
    """Get translation history for a segment"""
    segment = db.query(TranscriptSegment).filter(
        TranscriptSegment.id == segment_id
    ).first()
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )
    
    translations = db.query(Translation).filter(
        Translation.segment_id == segment_id
    ).order_by(Translation.created_at.desc()).all()
    
    return translations


@router.post("/segment/{segment_id}/retranslate", response_model=TranslationResponse)
async def retranslate_segment(
    segment_id: str,
    service: str = None,
    db: Session = Depends(get_db),
):
    """Retry translation for a segment"""
    segment = db.query(TranscriptSegment).filter(
        TranscriptSegment.id == segment_id
    ).first()
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )
    
    # Perform new translation
    translated_text = await translation_service.translate(
        text=segment.original_text,
        source_lang=segment.original_language,
        target_lang="en",
        service=service,
    )
    
    # Save translation
    translation = Translation(
        segment_id=segment.id,
        source_language=segment.original_language,
        target_language="en",
        source_text=segment.original_text,
        translated_text=translated_text["text"],
        translation_service=translated_text["service"],
        confidence_score=translated_text.get("confidence"),
        is_active=True,
    )
    
    # Mark previous translations as inactive
    db.query(Translation).filter(
        Translation.segment_id == segment.id,
        Translation.target_language == "en",
    ).update({"is_active": False})
    
    db.add(translation)
    
    # Update segment
    segment.translated_text = translated_text["text"]
    segment.translation_service = translated_text["service"]
    
    db.commit()
    db.refresh(translation)
    
    return translation
