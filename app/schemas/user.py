from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.user_provider import UserProviderResponse

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

# Novo schema para resposta completa com providers
class UserCompleteResponse(BaseModel):
    id: int
    username: str
    email: str
    firebase_uid: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    providers: List[UserProviderResponse]

    class Config:
        from_attributes = True

# Novo schema para busca por firebase_uid
class UserByFirebaseResponse(BaseModel):
    id: int
    username: str
    email: str
    firebase_uid: str
    providers: List[UserProviderResponse]

    class Config:
        from_attributes = True