"""
Database Schemas for Revelia.life

Pydantic models that define our MongoDB collections.
Each class name lowercased is used as the collection name
(e.g., Dream -> "dream").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict

class Lead(BaseModel):
    email: EmailStr = Field(..., description="Lead email")
    name: Optional[str] = Field(None, description="Optional name")
    language: Optional[str] = Field("es", description="Preferred language code: es, en, pt")
    source: Optional[str] = Field("landing", description="Where the lead came from")

class User(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    language: Optional[str] = Field("es")
    tier: str = Field("free", description="free | pro | premium")

class Dream(BaseModel):
    user_email: Optional[EmailStr] = Field(None, description="Email tying the dream to a user/lead")
    text: str = Field(..., description="Dream text content")
    language: str = Field("es", description="Input language code")
    analysis: Optional[Dict] = Field(None, description="Structured analysis result")
    audio_filename: Optional[str] = Field(None, description="If an audio file was uploaded")
    tags: Optional[List[str]] = Field(default_factory=list)

class QuizAnswer(BaseModel):
    user_email: EmailStr
    answers: Dict[str, str]
    score: Optional[int] = None

class Subscription(BaseModel):
    user_email: EmailStr
    tier: str = Field(..., description="free | pro | premium")
    status: str = Field("active")

class Report(BaseModel):
    user_email: EmailStr
    dream_id: Optional[str] = None
    subject: str
    content: str
    language: str = Field("es")
    delivered: bool = False
