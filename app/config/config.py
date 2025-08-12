from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    class Config:
        env_file = ".env"

settings = Settings()

print("Cloudinary Cloud Name:", settings.cloudinary_cloud_name)
print("Cloudinary API Key:", settings.cloudinary_api_key)
print("Cloudinary API Secret:", settings.cloudinary_api_secret)
