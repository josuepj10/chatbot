# models.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from decouple import config
from sqlalchemy.engine import URL
from settings import settings

# models.py

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from settings import settings


## 1) Construir la URL de conexión usando los valores de settings
url = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name
)

# 2) Crear el engine y SessionLocal
engine       = create_engine(url, echo=True)
SessionLocal = sessionmaker(bind=engine)

# 3) Base declarativa para todos los modelos
Base = declarative_base()

# 4) Modelo Client
class Client(Base):
    __tablename__ = "clients"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(Text, nullable=False, unique=True)
    api_key    = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    resources     = relationship(
        "ClientResource",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation",
        back_populates="client"
    )

# 5) Modelo ClientResource
class ClientResource(Base):
    __tablename__ = "client_resources"

    id         = Column(Integer, primary_key=True, index=True)
    client_id  = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name       = Column(Text, nullable=False)
    type       = Column(Text, nullable=False)
    content    = Column(Text, nullable=False)
    embedding  = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa
    client = relationship("Client", back_populates="resources")

# 6) Modelo Conversation (ahora con client_id)
class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    sender     = Column(Text, nullable=False)
    message    = Column(Text, nullable=False)
    response   = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client_id  = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    client     = relationship("Client", back_populates="conversations")