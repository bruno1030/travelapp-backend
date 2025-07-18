from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cities
from app.routers import photos
from app.routers import users

app = FastAPI()

# Inclusão das rotas
app.include_router(cities.router)
app.include_router(photos.router)
app.include_router(users.router)

# Configurar o middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (cuidado em produção)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota simples de teste
@app.get("/")
def read_root():
    return {"message": "Hello, world!"}

# Bloco necessário para rodar com uvicorn, incluindo Railway
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
