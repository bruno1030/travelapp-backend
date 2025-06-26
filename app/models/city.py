from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.photo import Photo

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)

    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id])
