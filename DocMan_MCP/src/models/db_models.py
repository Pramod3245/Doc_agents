
from datetime import datetime
from typing import Optional
from bson import ObjectId

class User:
    def __init__(self, username: str, email: str, hashed_password: str, created_at: datetime = None, id: ObjectId = None):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at if created_at is not None else datetime.utcnow()
        self.id = id

class Project:
    def __init__(self, name: str, owner_id: ObjectId, description: Optional[str] = None, created_at: datetime = None, id: ObjectId = None):
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.created_at = created_at if created_at is not None else datetime.utcnow()
        self.id = id

class Document:
    def __init__(self, title: str, file_path: str, owner_id: ObjectId, project_id: Optional[ObjectId] = None, uploaded_at: datetime = None, id: ObjectId = None):
        self.title = title
        self.file_path = file_path
        self.owner_id = owner_id
        self.project_id = project_id
        self.uploaded_at = uploaded_at if uploaded_at is not None else datetime.utcnow()
        self.id = id


