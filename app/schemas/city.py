from pydantic import BaseModel
from typing import Optional

class CityBase(BaseModel):
    name: str
    country: str

class CityResponse(CityBase):
    id: int
    cover_photo_url: Optional[str] = None  # Simples, derivado de `photo_url`

    class Config:
        orm_mode = True
