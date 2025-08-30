from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=True)  # Agora pode ser NULL para usuários do Google
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Novas colunas
    firebase_uid = Column(String, nullable=True, unique=True, index=True)  # UID do Firebase
    provider = Column(String, nullable=True, default="email")  # "email", "google", etc.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)