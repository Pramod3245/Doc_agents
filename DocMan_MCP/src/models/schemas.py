from pydantic import BaseModel, Field, EmailStr, model_validator
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.validate),
            json_schema=core_schema.str_schema(),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                lambda v, _: str(v), return_schema=core_schema.str_schema()
            )
        )

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class BaseModelWithConfig(BaseModel):
    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True

class UserBase(BaseModelWithConfig):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class User(UserBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    hashed_password: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def check_id(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict):
            if '_id' in data and isinstance(data['_id'], str):
                data['_id'] = ObjectId(data['_id'])
        return data

class DocumentBase(BaseModelWithConfig):
    title: str = Field(..., min_length=1, max_length=200)
    access: Literal["public", "private"] = Field(default="private")

class DocumentCreate(DocumentBase):
    project_id: Optional[PyObjectId] = None  # Optional project assignment during creation

class DocumentResponse(DocumentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    owner_id: PyObjectId
    project_id: Optional[PyObjectId] = None
    file_path: str  # Only in response, not in creation
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectBase(BaseModelWithConfig):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    access: Literal["public", "private"] = Field(default="private")

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    owner_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    members: List[PyObjectId] = Field(default_factory=list)  # List of user IDs

class ProjectResponse(Project):
    documents: List[DocumentResponse] = Field(default_factory=list)
    member_count: int = Field(default=0)

class UserInProject(BaseModelWithConfig):
    user_id: PyObjectId
    username: str
    email: EmailStr
    joined_at: datetime


