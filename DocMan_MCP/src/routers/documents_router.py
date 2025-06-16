from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status, BackgroundTasks
from typing import List
from src.models import schemas
from bson import ObjectId
from config.db import get_database
import os
from datetime import datetime
import shutil
from pathlib import Path
import subprocess
import sys

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("src/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/documents/", response_model=schemas.DocumentResponse)
async def create_document(
    title: str,
    file: UploadFile = File(...),
    project_id: str = None,
    access: str = "private",
    current_user_id: str = None,
    db = Depends(get_database)
):
    try:
        if not ObjectId.is_valid(current_user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
            
        if project_id and not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project ID")
            
        if project_id:
            # Check if project exists and user is member
            project = db.projects.find_one({
                "_id": ObjectId(project_id),
                "$or": [
                    {"owner_id": ObjectId(current_user_id)},
                    {"members": ObjectId(current_user_id)}
                ]
            })
            if not project:
                raise HTTPException(
                    status_code=403,
                    detail="Project not found or user is not a member"
                )

        # Create user folder if it doesn't exist
        user_upload_dir = UPLOAD_DIR / current_user_id
        user_upload_dir.mkdir(exist_ok=True)
        
        # Save file with timestamp to ensure unique names
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        safe_filename = timestamp + file.filename.replace(" ", "_")
        file_path = user_upload_dir / safe_filename
        
        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Copy PDF to /pdfs for ingestion
        pdfs_dir = Path("pdfs")
        pdfs_dir.mkdir(exist_ok=True)
        pdf_dest = pdfs_dir / safe_filename
        shutil.copy(str(file_path), str(pdf_dest))
            
        # Create document record
        doc_data = {
            "title": title,
            "file_path": str(file_path),
            "owner_id": ObjectId(current_user_id),
            "project_id": ObjectId(project_id) if project_id else None,
            "access": access,
            "uploaded_at": datetime.utcnow()
        }
        
        result = db.documents.insert_one(doc_data)
        new_doc = db.documents.find_one({"_id": result.inserted_id})
        return schemas.DocumentResponse(**new_doc)
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/projects/{project_id}/documents", response_model=List[schemas.DocumentResponse])
async def list_project_documents(
    project_id: str,
    current_user_id: str,
    db = Depends(get_database)
):
    try:
        if not all(ObjectId.is_valid(id) for id in [project_id, current_user_id]):
            raise HTTPException(status_code=400, detail="Invalid project or user ID")

        # Check if user has access to project
        project = db.projects.find_one({
            "_id": ObjectId(project_id),
            "$or": [
                {"owner_id": ObjectId(current_user_id)},
                {"members": ObjectId(current_user_id)}
            ]
        })
        
        if not project:
            raise HTTPException(
                status_code=403,
                detail="Project not found or user does not have access"
            )

        # Get all documents in the project
        documents = list(db.documents.find({
            "project_id": ObjectId(project_id)
        }))
        
        return [schemas.DocumentResponse(**doc) for doc in documents]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user_id: str, db = Depends(get_database)):
    try:
        if not ObjectId.is_valid(document_id):
            raise HTTPException(status_code=400, detail="Invalid document ID")
            
        # Get document and check ownership
        document = db.documents.find_one({
            "_id": ObjectId(document_id),
            "owner_id": ObjectId(current_user_id)
        })
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found or you don't have permission to delete it"
            )
            
        # Delete file from filesystem
        file_path = Path(document["file_path"])
        if file_path.exists():
            file_path.unlink()
            
        # Delete document record
        result = db.documents.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete document record"
            )
            
        return {"message": "Document deleted successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/documents/ingest")
async def ingest_pdfs(ingest: str):
    """Trigger ingestion of PDFs if ingest is 'yes'."""
    if ingest.lower() == "yes":
        python_path = sys.executable
        try:
            result = subprocess.run([python_path, "ingest_to_vector.py"], capture_output=True, text=True, check=True)
            return {"message": "Ingestion completed.", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"message": "Ingestion failed.", "error": e.stderr}
        except FileNotFoundError:
            return {"message": f"Python interpreter not found at {python_path}."}
    return {"message": "Ingestion not started. Send 'yes' to start."}