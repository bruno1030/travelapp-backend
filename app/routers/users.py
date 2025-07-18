from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found.")

    return [UserResponse(id=u.id, username=u.username, email=u.email) for u in users]
