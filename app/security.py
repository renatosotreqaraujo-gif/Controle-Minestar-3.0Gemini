"""
Autenticação simples baseada em sessão de cookie assinado (Starlette
SessionMiddleware). Sem necessidade de servidor de autenticação externo —
tudo fica no próprio banco local.

Perfis (role):
  admin     - tudo, incluindo cadastrar/editar/remover usuários
  operator  - tudo, exceto gerenciar usuários
  readonly  - só visualizar e testar ping (leitura)
"""
from datetime import datetime

from fastapi import Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db, User, AuditLog

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_READONLY = "readonly"
ALL_ROLES = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def ensure_default_admin(db: Session):
    """Cria o usuário admin padrão se ainda não existir nenhum usuário."""
    if db.query(User).count() == 0:
        db.add(User(
            username="admin",
            password_hash=hash_password("admin123"),
            role=ROLE_ADMIN,
        ))
        db.commit()


def log_action(db: Session, username: str, action: str, details: str = None):
    db.add(AuditLog(username=username, action=action, details=details))
    db.commit()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Não autenticado")
    user = db.query(User).get(user_id)
    if not user or not user.active:
        raise HTTPException(401, "Sessão inválida")
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).get(user_id)


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Você não tem permissão para essa ação")
        return user
    return dependency


# Atalhos comuns
require_admin = require_roles(ROLE_ADMIN)
require_operator_or_admin = require_roles(ROLE_ADMIN, ROLE_OPERATOR)
require_any = require_roles(*ALL_ROLES)
