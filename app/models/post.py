from datetime import datetime
from typing import Optional, Dict, Any

from bson import ObjectId
from pydantic import BaseModel, Field, validator, Json

# Validator for MongoDB ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Request model for scheduling a post
class SchedulePostRequest(BaseModel):
    platform: str = Field(..., description="Target platform (e.g., 'twitter', 'facebook')")
    content: Dict[str, Any] = Field(..., description="Platform-specific content for the post")
    scheduled_time: Optional[datetime] = Field(None, description="Time to post (UTC). If None, post immediately.")

# Response model after scheduling a post
class SchedulePostResponse(BaseModel):
    post_id: str = Field(..., description="The unique ID assigned to the scheduled post")
    status: str = Field(default="pending", description="Initial status of the post")
    message: str = Field(default="Post scheduled successfully", description="Confirmation message")

# Internal representation (potentially for DB storage, might need more fields)
class PostInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str # Link to the user who scheduled it
    platform: str
    content: Dict[str, Any]
    scheduled_time: Optional[datetime]
    status: str = Field(default="pending") # e.g., pending, processing, posted, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Add other fields like error_message, attempts, etc. if needed

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True # Needed for ObjectId
        json_encoders = {ObjectId: str}
