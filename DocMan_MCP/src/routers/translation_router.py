from fastapi import APIRouter, HTTPException, Query, Depends, Response, status
from typing import Dict, Any
from src.models import schemas
from src.services.translation_agent import TranslationAgent
from bson import ObjectId
from config.db import get_database
import os
import asyncio
from datetime import datetime
from pathlib import Path

router = APIRouter()
translation_agent = TranslationAgent()

# Create translations directory if it doesn't exist
TRANSLATIONS_DIR = Path("translations")
TRANSLATIONS_DIR.mkdir(exist_ok=True)

def get_translation_path(original_path: str, target_language: str, page: int = None, section: str = None) -> str:
    """Generate path for translated file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(original_path).stem
    
    if page is not None:
        filename = f"{timestamp}_{base_name}_page{page}_{target_language}.md"
    elif section is not None:
        safe_section = section.replace(" ", "_").replace("/", "_")[:30]
        filename = f"{timestamp}_{base_name}_section_{safe_section}_{target_language}.md"
    else:
        filename = f"{timestamp}_{base_name}_{target_language}.md"
    
    return str(TRANSLATIONS_DIR / filename)

def save_translation(translation_result: Dict[str, Any], save_path: str) -> None:
    """Save translation result as markdown with metadata"""
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            # Write metadata header
            f.write("---\n")
            f.write(f"original_file: {translation_result.get('original_file', 'N/A')}\n")
            f.write(f"target_language: {translation_result.get('target_language', 'N/A')}\n")
            f.write(f"translation_date: {datetime.now().isoformat()}\n")
            f.write(f"chunks_processed: {translation_result.get('chunks_processed', 0)}\n")
            if 'page_number' in translation_result:
                f.write(f"page: {translation_result['page_number']}\n")
            if 'section' in translation_result:
                f.write(f"section: {translation_result['section']}\n")
            f.write("---\n\n")
            # Write translated content
            f.write(translation_result.get('translation', ''))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving translation: {str(e)}"
        )

# --- Unified translation response builder ---
def build_translation_response(document, file_path, translation_result, extra: dict = None):
    resp = {
        "status": "success" if translation_result.get("success", True) else "error",
        "document_id": str(document.get("_id")),
        "title": document.get("title", ""),
        "original_file": file_path,
        "chunks_processed": translation_result.get("chunks_processed", 0),
        "translation": translation_result.get("translation", ""),
        "target_language": translation_result.get("target_language", "N/A")
    }
    if extra:
        resp.update(extra)
    return resp

@router.post("/documents/{document_id}/translate/document", response_model=Dict[str, Any])
async def translate_document(
    document_id: str,
    target_language: str = Query(..., min_length=2, description="Target language for translation (e.g., 'French')"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Translate the entire document."""
    try:
        if not ObjectId.is_valid(document_id):
            raise HTTPException(status_code=400, detail="Invalid document ID")
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        response.headers["X-Accel-Buffering"] = "no"
        # --- DRY RUN: If env var set, return dummy translation for test ---
        if os.getenv("TRANSLATION_DRY_RUN") == "1":
            translation_result = {"success": True, "translation": "[DRY RUN] Translated content.", "chunks_processed": 1, "target_language": target_language}
        else:
            translation_result = await asyncio.wait_for(
                translation_agent.translate_document(file_path, target_language),
                timeout=600
            )
        # Always add required fields for saving
        translation_result["original_file"] = file_path
        translation_result["target_language"] = target_language
        save_path = get_translation_path(file_path, target_language)
        save_translation(translation_result, save_path)
        resp = build_translation_response(document, file_path, translation_result, {"translated_file": save_path})
        return resp
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Translation timed out. Please try with a smaller section.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@router.post("/documents/{document_id}/translate/page", response_model=Dict[str, Any])
async def translate_page(
    document_id: str,
    page_number: int = Query(..., ge=0),
    target_language: str = Query(..., min_length=2, description="Target language for translation (e.g., 'French')"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Translate a specific page."""
    try:
        if not ObjectId.is_valid(document_id):
            raise HTTPException(status_code=400, detail="Invalid document ID")
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        response.headers["X-Accel-Buffering"] = "no"
        if os.getenv("TRANSLATION_DRY_RUN") == "1":
            translation_result = {"success": True, "translation": f"[DRY RUN] Translated page {page_number}.", "chunks_processed": 1, "target_language": target_language}
        else:
            translation_result = await asyncio.wait_for(
                translation_agent.translate_page(file_path, page_number, target_language),
                timeout=300
            )
        translation_result["original_file"] = file_path
        translation_result["target_language"] = target_language
        translation_result["page_number"] = page_number
        save_path = get_translation_path(file_path, target_language, page=page_number)
        save_translation(translation_result, save_path)
        resp = build_translation_response(document, file_path, translation_result, {"translated_file": save_path, "page_number": page_number})
        return resp
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Translation timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@router.post("/documents/{document_id}/translate/section", response_model=Dict[str, Any])
async def translate_section(
    document_id: str,
    section_text: str = Query(..., min_length=1, description="Text to identify the section"),
    target_language: str = Query(..., min_length=2, description="Target language for translation (e.g., 'French')"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Translate a specific section."""
    try:
        if not ObjectId.is_valid(document_id):
            raise HTTPException(status_code=400, detail="Invalid document ID")
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        response.headers["X-Accel-Buffering"] = "no"
        if os.getenv("TRANSLATION_DRY_RUN") == "1":
            translation_result = {"success": True, "translation": f"[DRY RUN] Translated section {section_text}.", "chunks_processed": 1, "target_language": target_language}
        else:
            translation_result = await asyncio.wait_for(
                translation_agent.translate_section(file_path, section_text, target_language),
                timeout=300
            )
        translation_result["original_file"] = file_path
        translation_result["target_language"] = target_language
        translation_result["section"] = section_text
        save_path = get_translation_path(file_path, target_language, section=section_text)
        save_translation(translation_result, save_path)
        resp = build_translation_response(document, file_path, translation_result, {"translated_file": save_path, "section": section_text})
        return resp
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Translation timed out. Please try with a shorter section.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")
