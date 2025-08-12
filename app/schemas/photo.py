from pydantic import BaseModel
from typing import Optional

class PhotoResponse(BaseModel):
    id: int
    image_url: str
    city_id: int
    latitude: float
    longitude: float
    user_id: int

    class Config:
        from_attributes = True
        
class PhotoCreate(BaseModel):
    image_url: str
    latitude: float
    longitude: float
    city_id: Optional[int] = None
    user_id: int
