from pydantic import BaseModel
from typing import Optional, List

class CityBase(BaseModel):
    name: str
    country: str

class TranslationResponse(BaseModel):
    language: str
    translated_name: str

class CityResponse(CityBase):
    id: int
    cover_photo_url: Optional[str] = None
    translations: Optional[List[TranslationResponse]] = []  # Lista de traduções

    class Config:
        orm_mode = True
