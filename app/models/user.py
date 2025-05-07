from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from app.models.post import PyObjectId # Reuse the ObjectId validator

class UserBase(BaseModel):
    username: str = Field(..., index=True)
    email: EmailStr = Field(..., index=True)
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

# Model stored in DB (includes hashed password)
class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True # Needed for ObjectId
        json_encoders = {ObjectId: str}

# Model returned by API (omits password)
class User(UserBase):
    id: str # Return ID as string

    class Config:
        orm_mode = True # Allows reading data from ORM models or other mappings
