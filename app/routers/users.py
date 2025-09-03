from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.models.user_provider import UserProvider
from app.schemas.user import UserResponse, UserCreate, EmailCheckResponse, UserCompleteResponse, UserByFirebaseResponse
from app.schemas.user_provider import UserProviderCreate
from datetime import datetime
import firebase_admin
from firebase_admin import auth as firebase_auth
import logging

# Configura logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa Firebase Admin SDK (uma vez)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

router = APIRouter()

@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        logger.info("No users found in database")
        raise HTTPException(status_code=404, detail="No users found.")
    logger.info(f"Retrieved {len(users)} users from database")
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
    logger.info(f"Received request to create user from Firebase: {user_data.email}")

    if not authorization.startswith("Bearer "):
        logger.warning("Authorization header missing or invalid")
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split("Bearer ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]
        logger.info(f"Firebase token verified successfully for UID: {firebase_uid}")
    except Exception as e:
        logger.error(f"Failed to verify Firebase ID token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Firebase ID token: {str(e)}")

    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        logger.warning(f"Firebase UID {firebase_uid} already exists in database")
        raise HTTPException(status_code=400, detail="Firebase UID already exists")

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Email {user_data.email} already exists in database")
        raise HTTPException(status_code=400, detail="Email already exists")

    username = user_data.username
    if username and db.query(User).filter(User.username == username).first():
        logger.warning(f"Username {username} already exists in database")
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        new_user = User(
            firebase_uid=firebase_uid,
            email=user_data.email,
            username=username,
            last_login=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()
        logger.info(f"New user object created: {new_user}")

        user_provider = UserProvider(
            user_id=new_user.id,
            provider=user_data.provider,
            provider_uid=firebase_uid
        )
        db.add(user_provider)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User {new_user.id} saved successfully with provider {user_data.provider}")

        return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": username,
            "firebase_uid": new_user.firebase_uid
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user in database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/users/current", response_model=UserByFirebaseResponse)
def get_current_user(
    authorization: str = Header(...), 
    db: Session = Depends(get_db)
):
    logger.info("Received request to fetch current user")

    if not authorization.startswith("Bearer "):
        logger.warning("Authorization header missing or invalid for current user endpoint")
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split(" ")[1]

    try:
        decoded_token = firebase_admin.auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]
        logger.info(f"Token verified for current user UID: {firebase_uid}")
    except Exception as e:
        logger.error(f"Invalid ID token for current user: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        logger.warning(f"User with UID {firebase_uid} not found in database")
        raise HTTPException(status_code=404, detail="User not found")

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    logger.info(f"Updated last_login for user {user.id}")

    return user

@router.get("/users/{user_id}/complete", response_model=UserCompleteResponse)
def get_user_complete(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User with ID {user_id} not found for complete info endpoint")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Retrieved complete info for user {user_id}")
    return user

@router.post("/users/create", status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Email {user_data.email} already exists for create user endpoint")
        raise HTTPException(status_code=400, detail="Email already exists")

    username = user_data.username
    if username and db.query(User).filter(User.username == username).first():
        logger.warning(f"Username {username} already exists for create user endpoint")
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
    logger.info(f"User {new_user.id} created successfully with username {username}")
    return {"message": "User created successfully", "user_id": new_user.id, "username": username}
