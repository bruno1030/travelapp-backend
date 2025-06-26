from fastapi import FastAPI
from app.routers import cities
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(cities.router)

# Configurar o middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Isso permite todos os domínios (não recomendado para produção)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos os headers
)

@app.get("/")
def read_root():
    return {"message": "Hello, world!"}