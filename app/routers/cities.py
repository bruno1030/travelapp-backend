from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.models.city import City
from app.schemas.city import CityResponse, TranslationResponse

router = APIRouter()

@router.get("/cities", response_model=list[CityResponse])
def get_all_cities(
    db: Session = Depends(get_db)
):
    # Carregar todas as cidades, incluindo as traduções e as fotos
    cities = db.query(City).options(joinedload(City.cover_photo), joinedload(City.translations)).all()

    result = []

    for city in cities:
        # Criar uma lista de traduções para a cidade
        translations = [
            TranslationResponse(language=t.language, translated_name=t.translated_name)
            for t in city.translations
        ]
        
        result.append(
            CityResponse(
                id=city.id,
                name=city.name,
                country=city.country,
                cover_photo_url=city.cover_photo.image_url if city.cover_photo else None,
                translations=translations  # Retornando todas as traduções
            )
        )
    
    return result
