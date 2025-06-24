from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from typing import List
from src.models import schemas
from bson import ObjectId
from config.db import get_database
from datetime import datetime
from src.utils.otel_tracing import traced_function
from src.utils.jwt_auth import create_access_token, get_password_hash, verify_password

router = APIRouter()

@router.post("/users/", response_model=schemas.User)
@traced_function()
async def create_user(user: schemas.UserCreate, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        # Check if user already exists
        existing_user = db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user.password)
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
        result = db.users.insert_one(user_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
        new_user = db.users.find_one({"_id": result.inserted_id})
        return schemas.User(**new_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/token")
@traced_function()
async def login_for_access_token(response: Response, db = Depends(get_database), username: str = None, password: str = None):
    user = db.users.find_one({"username": username})
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token({"user_name": str(user["username"])})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/{user_id}/projects", response_model=List[schemas.Project])
@traced_function()
async def list_user_projects(user_id: str, db = Depends(get_database), request: Request = None, session_id: str = None):
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Find projects where user is owner or member
        user_projects = list(db.projects.find({
            "$or": [
                {"owner_id": ObjectId(user_id)},
                {"members": ObjectId(user_id)}
            ]
        }))
        return [schemas.Project(**project) for project in user_projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/users/{user_id}/documents", response_model=List[schemas.DocumentResponse])
@traced_function()
async def list_user_documents(
    user_id: str, 
    include_project_docs: bool = False,
    db = Depends(get_database),
    request: Request = None,
    session_id: str = None
):
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        # Get user's direct documents
        query = {"owner_id": ObjectId(user_id)}
        
        if include_project_docs:
            # Get user's project memberships
            projects = [p["_id"] for p in db.projects.find({
                "$or": [
                    {"owner_id": ObjectId(user_id)},
                    {"members": ObjectId(user_id)}
                ]
            }, {"_id": 1})]
            
            # Include documents from user's projects
            if projects:
                query = {
                    "$or": [
                        {"owner_id": ObjectId(user_id)},
                        {"project_id": {"$in": projects}}
                    ]
                }
        
        documents = list(db.documents.find(query))
        return [schemas.DocumentResponse(**doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

