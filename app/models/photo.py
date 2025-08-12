from sqlalchemy import Column, Integer, String, Float
from app.db import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    city_id = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=True)
