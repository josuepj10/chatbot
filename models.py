# models.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from decouple import config

# 1) Construir la URL de conexión leyendo del .env
url = URL.create(
    drivername="postgresql",
    username=config("DB_USER"),
    password=config("DB_PASSWORD"),
    host=config("DB_HOST", default="localhost"),
    port=config("DB_PORT", cast=int, default=5432),
    database=config("DB_NAME"),
)

# 2) Crear el engine y la fábrica de sesiones
engine       = create_engine(url)
SessionLocal = sessionmaker(bind=engine)

# 3) Base declarativa para tus modelos
Base = declarative_base()

# 4) Definir el modelo Conversation
class Conversation(Base):
    __tablename__ = "conversations"

    id       = Column(Integer, primary_key=True, index=True)
    sender   = Column(String)
    message  = Column(String)
    response = Column(String)

# 5) Crear la tabla en la BD (si no existe)
Base.metadata.create_all(engine)
print("✅ Tabla 'conversations' lista en la base de datos.")
