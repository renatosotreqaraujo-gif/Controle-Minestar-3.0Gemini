"""
Camada de banco de dados (v4).

Estrutura:
  Equipment  -> um equipamento físico (ex: CA101, um caminhão 793F)
  Asset      -> um dos ativos de rede do equipamento (MEMS, DISPLAY, DIM/RIM/PLE, AVI LTE)
  PingResult -> histórico de ping de um Asset
  User       -> usuário do sistema (admin / operador / leitura)
  AuditLog   -> log de ações importantes dos usuários
"""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from .paths import data_dir

DB_PATH = os.path.join(data_dir(), "ping_tool.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String(40), nullable=False, unique=True, index=True)   # ex: CA101
    model = Column(String(80), default="")                              # ex: 793F
    machine_type = Column(String(80), default="Outro / Não Classificado")
    icon = Column(String(40), default="generic")
    active = Column(Boolean, default=True)

    assets = relationship("Asset", back_populates="equipment", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("equipment_id", "asset_type", name="uq_equipment_asset_type"),)

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, index=True)
    asset_type = Column(String(30), nullable=False)   # MEMS, DISPLAY, DIM_RIM_PLE, AVI_LTE
    display_model = Column(String(20), nullable=True)  # G407 / G610, só quando asset_type == DISPLAY
    ip = Column(String(45), nullable=True, index=True)
    active = Column(Boolean, default=True)

    # cache do último resultado
    last_status = Column(Boolean, nullable=True)
    last_rtt_ms = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)   # sempre em UTC
    consecutive_failures = Column(Integer, default=0)

    equipment = relationship("Equipment", back_populates="assets")
    history = relationship("PingResult", back_populates="asset", cascade="all, delete-orphan")


class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # UTC
    is_alive = Column(Boolean, nullable=False)
    rtt_ms = Column(Float, nullable=True)
    packet_loss = Column(Float, nullable=True)

    asset = relationship("Asset", back_populates="history")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(60), nullable=False, unique=True, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="readonly")  # admin | operator | readonly
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # UTC
    username = Column(String(60), nullable=False)
    action = Column(String(80), nullable=False)
    details = Column(String(400), nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
