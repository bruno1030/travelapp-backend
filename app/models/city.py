from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.photo import Photo

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)

    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id], uselist=False)
    translations = relationship("CityTranslation", back_populates="city", cascade="all, delete-orphan")

class CityTranslation(Base):
    __tablename__ = "city_translations"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    language = Column(String, nullable=False)  # Ex: 'pt', 'ja', etc.
    translated_name = Column(String, nullable=False)

    city = relationship("City", back_populates="translations")

    __table_args__ = (UniqueConstraint("city_id", "language", name="uix_city_language"),)
