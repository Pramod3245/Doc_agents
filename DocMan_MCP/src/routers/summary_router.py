from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks, Response
from typing import Optional, Dict, Any
from src.models import schemas
from src.services.summarization.summary_agent import SummaryAgent
from bson import ObjectId
from config.db import get_database
import os
import asyncio

router = APIRouter()
summary_agent = SummaryAgent()

@router.post("/documents/{document_id}/summarize/page", response_model=Dict[str, Any])
async def summarize_page(
    document_id: str,
    page_number: int = Query(..., ge=0),
    detailed: bool = Query(False, description="Whether to generate a detailed summary"),
    style: str = Query("professional", description="Summary style (professional, casual, technical)"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Generate a summary of a specific page from a document."""
    try:
        # Set a longer timeout for the response
        response.headers["X-Accel-Buffering"] = "no"
        
        # Verify document exists and user has access
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
            
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )
        
        # Generate summary with timeout handling
        try:
            summary = await asyncio.wait_for(
                summary_agent.summarize_page(
                    file_path,
                    page_number,
                    detailed=detailed,
                    style=style
                ),
                timeout=300  # 5 minutes timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Summary generation timed out. Please try again with a smaller section."
            )
            
        return {
            "status": "success",
            "document_id": str(document_id),
            "page_number": page_number,
            "summary": summary["summary"],
            "metadata": {
                "title": document.get("title", ""),
                "style": style,
                "detailed": detailed,
                **summary.get("metadata", {})
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

@router.post("/documents/{document_id}/summarize/section", response_model=Dict[str, Any])
async def summarize_section(
    document_id: str,
    section_text: str = Query(..., min_length=1, description="Text to identify the section"),
    detailed: bool = Query(False, description="Whether to generate a detailed summary"),
    style: str = Query("professional", description="Summary style (professional, casual, technical)"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Generate a summary of a specific section from a document."""
    try:
        # Set a longer timeout for the response
        response.headers["X-Accel-Buffering"] = "no"
        
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
            
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )
            
        # Generate summary with timeout handling
        try:
            summary = await asyncio.wait_for(
                summary_agent.summarize_section(
                    file_path,
                    section_text,
                    detailed=detailed,
                    style=style
                ),
                timeout=300  # 5 minutes timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Summary generation timed out. Please try again with a smaller section."
            )
            
        return {
            "status": "success",
            "document_id": str(document_id),
            "section_text": section_text,
            "summary": summary["summary"],
            "metadata": {
                "title": document.get("title", ""),
                "style": style,
                "detailed": detailed,
                **summary.get("metadata", {})
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

@router.post("/documents/{document_id}/summarize/full", response_model=Dict[str, Any])
async def summarize_document(
    document_id: str,
    detailed: bool = Query(False, description="Whether to generate a detailed summary"),
    style: str = Query("professional", description="Summary style (professional, casual, technical)"),
    focus: str = Query("main points", description="What to focus on in the summary"),
    current_user_id: str = None,
    response: Response = None,
    db = Depends(get_database)
):
    """Generate a summary of the entire document."""
    try:
        # Set a longer timeout for the response
        response.headers["X-Accel-Buffering"] = "no"
        
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"access": "public"}
            ]
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
            
        file_path = document["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )
            
        # Generate summary with timeout handling
        try:
            summary = await asyncio.wait_for(
                summary_agent.summarize_document(
                    file_path,
                    detailed=detailed,
                    style=style,
                    focus=focus
                ),
                timeout=600  # 10 minutes timeout for full documents
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Summary generation timed out. Please try again with a smaller document or contact support."
            )
            
        return {
            "status": "success",
            "document_id": str(document_id),
            "summary": summary["summary"],
            "metadata": {
                "title": document.get("title", ""),
                "style": style,
                "detailed": detailed,
                "focus": focus,
                **summary.get("metadata", {})
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

