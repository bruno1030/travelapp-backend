import time
import hashlib
from app.config.config import settings

def generate_signature(folder: str = "travelapp", public_id: str | None = None):
    timestamp = int(time.time())

    # Parâmetros que vão ser assinados (Cloudinary exige ordem alfabética)
    params_to_sign = {
        "folder": folder,
        "timestamp": timestamp
    }
    if public_id:
        params_to_sign["public_id"] = public_id

    # Monta string ordenada
    sorted_params = sorted(params_to_sign.items())
    to_sign = "&".join(f"{k}={v}" for k, v in sorted_params)

    # Adiciona API_SECRET e gera SHA1
    signature = hashlib.sha1(f"{to_sign}{settings.cloudinary_api_secret}".encode()).hexdigest()

    return {
        "cloud_name": settings.cloudinary_cloud_name,
        "api_key": settings.cloudinary_api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": folder,
        "public_id": public_id
    }
