from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexão com o PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234590@localhost:5432/postgres"

# Criação do engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Sessão do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base dos modelos
Base = declarative_base()

# Dependência que será usada nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
