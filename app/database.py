"""
Camada de banco de dados.
Usa SQLite por padrão (arquivo local, zero configuração).
Se no futuro quiser plugar no SQL Server do fleet monitoring,
basta trocar a DATABASE_URL abaixo por uma connection string
do SQL Server (ex: usando pyodbc/mssql+pyodbc://...).
"""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from .paths import data_dir

DB_PATH = os.path.join(data_dir(), "ping_tool.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    ip = Column(String(45), nullable=False, unique=True, index=True)
    group = Column(String(80), default="Geral")  # ex: frota, escritório, torre
    active = Column(Boolean, default=True)

    # Estado calculado em memória / cache do último resultado
    last_status = Column(Boolean, nullable=True)   # True=online, False=offline, None=desconhecido
    last_rtt_ms = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)

    history = relationship(
        "PingResult", back_populates="asset", cascade="all, delete-orphan"
    )


class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    is_alive = Column(Boolean, nullable=False)
    rtt_ms = Column(Float, nullable=True)
    packet_loss = Column(Float, nullable=True)  # 0.0 a 1.0

    asset = relationship("Asset", back_populates="history")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
