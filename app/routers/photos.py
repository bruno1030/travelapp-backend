from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.photo import Photo
from app.models.city import City, CityTranslation
from app.schemas.photo import PhotoResponse, PhotoCreate
import httpx  # para chamadas externas
from typing import Optional

router = APIRouter()

@router.get("/photos/by_city/{city_id}", response_model=list[PhotoResponse])
def get_photos_by_city(city_id: int, db: Session = Depends(get_db)):
    print(f"Fetching photos for city_id: {city_id}")
    photos = db.query(Photo).filter(Photo.city_id == city_id).all()

    if not photos:
        print(f"No photos found for city_id: {city_id}")
        raise HTTPException(status_code=404, detail="No photos found for this city.")

    print(f"Found {len(photos)} photos for city_id: {city_id}")
    return [
        PhotoResponse.from_orm(photo)
        for photo in photos
    ]

@router.post("/photos", response_model=PhotoResponse)
def create_photo(photo_data: PhotoCreate, db: Session = Depends(get_db)):
    print(f"Starting photo creation process for coordinates: ({photo_data.latitude}, {photo_data.longitude})")
    city_name, country_name = get_city_and_country(photo_data.latitude, photo_data.longitude)
    print(f"Got city and country from API: city='{city_name}', country='{country_name}'")

    if not city_name or not country_name:
        print("City or country not found for given coordinates")
        raise HTTPException(status_code=400, detail="City not found for given coordinates")

    city = db.query(City).filter(
        City.name == city_name,
        City.country == country_name
    ).first()

    if not city:
        print(f"City '{city_name}' in country '{country_name}' not found in DB. Creating new city.")
        # Cria cidade sem cover_photo_id
        city = City(name=city_name, country=country_name, cover_photo_id=None)
        db.add(city)
        db.commit()
        db.refresh(city)
        print(f"Created city with ID: {city.id}")

        # Criar traduções da cidade
        translations = create_city_translations(city_name, city.id)
        db.add_all(translations)
        db.commit()
        print(f"Created {len(translations)} translations for city ID {city.id}")
    else:
        print(f"City found in DB with ID: {city.id}")

    # Cria foto vinculada à cidade
    new_photo = Photo(
        image_url=photo_data.image_url,
        latitude=photo_data.latitude,
        longitude=photo_data.longitude,
        city_id=city.id,
        user_id=photo_data.user_id
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    print(f"Created photo with ID: {new_photo.id} for city ID: {city.id}")

    # Atualiza cover_photo_id da cidade com o id da foto recém criada, se estiver nulo
    if city.cover_photo_id is None:
        city.cover_photo_id = new_photo.id
        db.commit()
        db.refresh(city)
        print(f"Updated city ID {city.id} cover_photo_id to photo ID {new_photo.id}")

    return PhotoResponse.from_orm(new_photo)


def create_city_translations(city_name: str, city_id: int) -> list[CityTranslation]:
    print(f"Creating translations for city '{city_name}' (ID: {city_id})")
    languages = ["en", "pt", "ja", "zh"]
    translations = []

    # Para todas as línguas, salva o nome em inglês mesmo
    for lang in languages:
        translations.append(CityTranslation(city_id=city_id, language=lang, translated_name=city_name))

    print(f"Translations created: {[t.language for t in translations]}")
    return translations

def get_city_and_country(latitude: float, longitude: float) -> Optional[tuple[str, str]]:
    print(f"Fetching city and country for lat={latitude}, lon={longitude} from Nominatim API")
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "accept-language": "en"  # idioma inglês
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        address = data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village")
        country = address.get("country")

        print(f"Received address info: city='{city}', country='{country}'")

        if city and country:
            return city, country
    except Exception as e:
        print(f"Error fetching city and country: {e}")

    return None
