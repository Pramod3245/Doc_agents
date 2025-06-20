from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from src.models import schemas
from bson import ObjectId
from config.db import get_database
from datetime import datetime
from src.utils.otel_tracing import traced_function

router = APIRouter()

@router.post("/projects/", response_model=schemas.Project)
@traced_function()
async def create_project(project: schemas.ProjectCreate, current_user_id: str, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        if not ObjectId.is_valid(current_user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        project_data = project.model_dump()
        project_data["owner_id"] = ObjectId(current_user_id)
        project_data["created_at"] = datetime.utcnow()
        project_data["members"] = []  # Initialize empty members list
        
        result = db.projects.insert_one(project_data)
        new_project = db.projects.find_one({"_id": result.inserted_id})
        return schemas.Project(**new_project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/projects/{project_id}/members/{user_id}")
@traced_function()
async def add_project_member(project_id: str, user_id: str, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        if not all(ObjectId.is_valid(id) for id in [project_id, user_id]):
            raise HTTPException(status_code=400, detail="Invalid project or user ID")
        
        # Check if project exists
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if user exists
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add user to project members if not already a member
        result = db.projects.update_one(
            {
                "_id": ObjectId(project_id),
                "members": {"$ne": ObjectId(user_id)}
            },
            {
                "$push": {"members": ObjectId(user_id)}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="User is already a member or project update failed")
            
        return {"message": "User added to project successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/projects/{project_id}/members", response_model=List[schemas.UserInProject])
@traced_function()
async def list_project_members(project_id: str, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project ID")
        
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get all members including owner
        member_ids = project.get("members", []) + [project["owner_id"]]
        members = list(db.users.find({"_id": {"$in": member_ids}}))
        
        return [
            schemas.UserInProject(
                user_id=member["_id"],
                username=member["username"],
                email=member["email"],
                joined_at=member.get("created_at", datetime.utcnow())
            )
            for member in members
        ]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.delete("/projects/{project_id}/members/{user_id}")
@traced_function()
async def remove_project_member(project_id: str, user_id: str, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        if not all(ObjectId.is_valid(id) for id in [project_id, user_id]):
            raise HTTPException(status_code=400, detail="Invalid project or user ID")
        
        # Check if project exists
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Cannot remove the owner
        if project["owner_id"] == ObjectId(user_id):
            raise HTTPException(status_code=400, detail="Cannot remove project owner")
        
        result = db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$pull": {"members": ObjectId(user_id)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="User is not a member or update failed")
            
        return {"message": "User removed from project successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

