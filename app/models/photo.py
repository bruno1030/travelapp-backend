from sqlalchemy import Column, Integer, String
from app.db import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
