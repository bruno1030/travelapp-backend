from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.models.city import City
from app.schemas.city import CityResponse

router = APIRouter()

@router.get("/cities", response_model=list[CityResponse])
def get_all_cities(db: Session = Depends(get_db)):
    # Carrega a cidade e a foto de capa associada com uma única consulta
    cities = db.query(City).options(joinedload(City.cover_photo)).all()
    
    result = []

    for city in cities:
        result.append(
            CityResponse(
                id=city.id,
                name=city.name,
                country=city.country,
                cover_photo_url=city.cover_photo.image_url if city.cover_photo else None
            )
        )
    
    return result
