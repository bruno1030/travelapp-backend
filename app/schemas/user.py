from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema existente - não mexemos
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

# Novos schemas para os endpoints
class UserCreate(BaseModel):
    firebase_uid: str
    email: str
    username: Optional[str] = None
    name: Optional[str] = None
    provider: str = "email"

class EmailCheckResponse(BaseModel):
    exists: bool
    email: str