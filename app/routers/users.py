import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.db import get_db
from app.models.user import User
from app.models.user_provider import UserProvider
from app.schemas.user import (
    UserResponse,
    UserCreate,
    EmailCheckResponse,
    UserCompleteResponse,
    UserByFirebaseResponse,
    UserUpdateRequest
)
from app.schemas.user_provider import UserProviderCreate

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import logging

# Configura logging
logger = logging.getLogger("app.routers.users")
logging.basicConfig(level=logging.INFO)

# Carrega variáveis do .env
load_dotenv()
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

# Inicializa Firebase Admin SDK com service account
if not firebase_admin._apps:
    if FIREBASE_SERVICE_ACCOUNT:
        try:
            cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {"projectId": GOOGLE_CLOUD_PROJECT})
            logger.info("Firebase Admin initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {str(e)}")
    else:
        logger.error("FIREBASE_SERVICE_ACCOUNT is not set in environment variables")

router = APIRouter()

# ---------------------------
# Endpoints
# ---------------------------

@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found.")
    return [UserResponse(id=u.id, username=u.username, email=u.email) for u in users]

@router.get("/users/check-email", response_model=EmailCheckResponse)
def check_email_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.info(f"Email {email} exists in database")
        return EmailCheckResponse(exists=True, email=email)
    else:
        logger.info(f"Email {email} does not exist in database")
        raise HTTPException(
            status_code=404,
            detail=EmailCheckResponse(exists=False, email=email).dict()
        )

@router.post("/users/create-from-firebase", status_code=201)
def create_user_from_firebase(
    user_data: UserCreate,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    import logging
    logger = logging.getLogger("app.routers.users")

    if not authorization.startswith("Bearer "):
        logger.error("Invalid authorization header")
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split("Bearer ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]  # UID confiável do token
        logger.info(f"Firebase ID token verified for UID: {firebase_uid}")
    except Exception as e:
        logger.error(f"Failed to verify Firebase ID token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Firebase ID token: {str(e)}")

    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        logger.warning(f"Firebase UID already exists: {firebase_uid}")
        raise HTTPException(status_code=400, detail="Firebase UID already exists")

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already exists")

    username = user_data.username
    if not username or username.strip() == "":
        username = f"user_{firebase_uid[:6]}"
        logger.info(f"No username provided, generated provisional username: {username}")

    if db.query(User).filter(User.username == username).first():
        logger.warning(f"Generated username already exists: {username}")
        raise HTTPException(status_code=400, detail="Generated username already exists, try again")

    try:
        new_user = User(
            firebase_uid=firebase_uid,
            email=user_data.email,
            username=username,
            last_login=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()
        logger.info(f"User object added to session: {username}")

        user_provider = UserProvider(
            user_id=new_user.id,
            provider=user_data.provider,
            provider_uid=firebase_uid
        )
        db.add(user_provider)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User successfully created in DB: {username} (UID: {firebase_uid})")

        return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": username,
            "firebase_uid": new_user.firebase_uid
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/users/current", response_model=UserByFirebaseResponse)
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split(" ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]
        logger.info(f"Current user token verified for UID: {firebase_uid}")
    except Exception as e:
        logger.error(f"Invalid ID token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user

@router.get("/users/{user_id}/complete", response_model=UserCompleteResponse)
def get_user_complete(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users/create", status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    username = user_data.username
    if username and db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        firebase_uid=user_data.firebase_uid,
        email=user_data.email,
        username=username,
        provider=user_data.provider
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id, "username": username}

@router.patch("/users/update", response_model=UserResponse)
def update_user(
    user_update: UserUpdateRequest,
    firebase_uid: str = Header(..., description="Firebase UID do usuário"),
    db: Session = Depends(get_db)
):
    """
    Atualiza o usuário com base no firebase_uid fornecido no header.
    Campos opcionais que podem ser atualizados: username, name
    """
    if not firebase_uid or firebase_uid.strip() == "":
        raise HTTPException(status_code=400, detail="Firebase UID é obrigatório no header")

    # Busca usuário no banco
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza campos se fornecidos
    if user_update.username:
        existing_user = (
            db.query(User)
            .filter(User.username == user_update.username, User.id != user.id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_update.username

    if user_update.name:
        user.name = user_update.name

    user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email
    )