from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserProviderBase(BaseModel):
    provider: str
    provider_uid: Optional[str] = None

class UserProviderCreate(UserProviderBase):
    user_id: int

class UserProviderResponse(UserProviderBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True