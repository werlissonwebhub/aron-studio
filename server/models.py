from typing import Optional
from pydantic import BaseModel

class AuthRequest(BaseModel):
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    email_verified: bool = False

class ChatInitRequest(BaseModel):
    first_prompt: str
    mode: str
    user_id: Optional[str] = None

class GenerationRequest(BaseModel):
    chat_id: str
    prompt: str
    user_id: str
    mode: str = "assistant"
    model_alias: str = "claude-sonnet-4-6"
    image_data: Optional[str] = None

class ProjectModel(BaseModel):
    chat_id: str
    user_id: str
    full_code: str

class ExtractionRequest(BaseModel):
    html: str
    user_id: str

class PlanRequest(BaseModel):
    prompt: str
    user_id: str

class RefundRequest(BaseModel):
    user_id: str
    reason: str
