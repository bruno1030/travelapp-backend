from pydantic import BaseModel

class PhotoResponse(BaseModel):
    id: int
    image_url: str
    city_id: int
    latitude: float
    longitude: float

    class Config:
        orm_mode = True
