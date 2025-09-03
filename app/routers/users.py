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

# Inicializa Firebase Admin SDK (uma vez)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

router = APIRouter()

# Endpoint existente - não mexemos
@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found.")
    return [UserResponse(id=u.id, username=u.username, email=u.email) for u in users]

# Endpoint existente - verificar se email existe
@router.get("/users/check-email", response_model=EmailCheckResponse)
def check_email_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return EmailCheckResponse(exists=True, email=email)
    else:
        raise HTTPException(
            status_code=404,
            detail=EmailCheckResponse(exists=False, email=email).dict()
        )

# NOVO ENDPOINT - Criar usuário após autenticação Firebase
@router.post("/users/create-from-firebase", status_code=201)
def create_user_from_firebase(
    user_data: UserCreate,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Cria um novo usuário no banco após autenticação Firebase.
    Recebe idToken no header Authorization e valida.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split("Bearer ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase ID token: {str(e)}")

    # Verificar se usuário já existe
    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Firebase UID already exists")

    # Verificar se email já existe
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Se username foi informado, validar se já existe
    username = user_data.username
    if username and db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        # Criar novo usuário
        new_user = User(
            firebase_uid=firebase_uid,
            email=user_data.email,
            username=username,
            last_login=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()  # Para obter o ID sem commit completo

        # Criar registro na tabela user_providers
        user_provider = UserProvider(
            user_id=new_user.id,
            provider=user_data.provider,
            provider_uid=firebase_uid
        )
        db.add(user_provider)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": username,
            "firebase_uid": new_user.firebase_uid
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

# Endpoint buscar usuário atual via idToken
@router.get("/users/current", response_model=UserByFirebaseResponse)
def get_current_user(
    authorization: str = Header(...), 
    db: Session = Depends(get_db)
):
    """
    Retorna o usuário atual autenticado pelo Firebase ID token.
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    id_token = authorization.split(" ")[1]

    try:
        # Verifica o token com Firebase Admin SDK
        decoded_token = firebase_admin.auth.verify_id_token(id_token)
        firebase_uid = decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")

    # Busca o usuário no banco usando o UID confiável
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza last_login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user

# Buscar usuário completo por ID (debug)
@router.get("/users/{user_id}/complete", response_model=UserCompleteResponse)
def get_user_complete(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Endpoint original - mantido para compatibilidade
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
