from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.photo import Photo
from app.schemas.photo import PhotoResponse
from fastapi import HTTPException
from app.models.photo import Photo

router = APIRouter()

@router.get("/photos/by_city/{city_id}", response_model=list[PhotoResponse])
def get_photos_by_city(city_id: int, db: Session = Depends(get_db)):
    photos = db.query(Photo).filter(Photo.city_id == city_id).all()

    if not photos:
        raise HTTPException(status_code=404, detail="No photos found for this city.")

    return [
        PhotoResponse(
            id=photo.id,
            image_url=photo.image_url,
            city_id=photo.city_id,
            latitude=photo.latitude,
            longitude=photo.longitude,
        )
        for photo in photos
    ]
