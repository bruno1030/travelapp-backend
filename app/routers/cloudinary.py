from fastapi import APIRouter, Depends
from app.utils.cloudinary_utils import generate_signature

router = APIRouter()

# Aqui você poderia ter Depends(get_current_user) para autenticação
@router.post("/cloudinary/signature")
def get_cloudinary_signature():
    # Aqui poderia gerar public_id único baseado no user_id
    # public_id = f"travelapp/user_{current_user.id}/uuidgerado"
    public_id = None  # temporário sem user
    data = generate_signature(public_id=public_id)
    return data
