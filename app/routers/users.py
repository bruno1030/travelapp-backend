from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, EmailCheckResponse

router = APIRouter()

# Endpoint existente - não mexemos
@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found.")

    return [UserResponse(id=u.id, username=u.username, email=u.email) for u in users]

# Novo endpoint - verificar se email existe
@router.get("/users/check-email", response_model=EmailCheckResponse)
def check_email_exists(email: str, db: Session = Depends(get_db)):
    """
    Verifica se um email já existe no banco de dados.
    Retorna 200 se existe, 404 se não existe.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        return EmailCheckResponse(exists=True, email=email)
    else:
        raise HTTPException(
            status_code=404, 
            detail=EmailCheckResponse(exists=False, email=email).dict()
        )

# Novo endpoint - criar usuário
@router.post("/users/create", status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário no banco de dados.
    """
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Verificar se firebase_uid já existe
    existing_firebase_user = db.query(User).filter(User.firebase_uid == user_data.firebase_uid).first()
    if existing_firebase_user:
        raise HTTPException(status_code=400, detail="Firebase UID already exists")
    
    # Gerar username se não fornecido
    username = user_data.username
    if not username:
        # Se não forneceu username, usar parte do email
        username = user_data.email.split('@')[0]
        
        # Verificar se username já existe, se sim, adicionar número
        counter = 1
        original_username = username
        while db.query(User).filter(User.username == username).first():
            username = f"{original_username}{counter}"
            counter += 1
    
    # Verificar se username escolhido já existe
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Criar novo usuário
    new_user = User(
        firebase_uid=user_data.firebase_uid,
        email=user_data.email,
        username=username,
        provider=user_data.provider,
        password_hash=None  # Será NULL para usuários do Firebase
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id, "username": username}