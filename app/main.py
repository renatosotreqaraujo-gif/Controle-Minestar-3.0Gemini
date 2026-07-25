import asyncio
import io
import os
import secrets
from datetime import datetime, timedelta

import pandas as pd
from fastapi import (
    FastAPI, Depends, UploadFile, File, HTTPException, WebSocket,
    WebSocketDisconnect, Request, Response
)
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from .database import init_db, get_db, SessionLocal, Equipment, Asset, PingResult, User, AuditLog
from .ping_service import ping_batch
from .ws_manager import manager
from .importers import import_equipment_from_excel
from .paths import static_dir, data_dir
from .equipment_types import ASSET_TYPE_LABELS
from .timezone_utils import to_brasilia, now_utc
from .monitoring import controller, CYCLE_SECONDS
from .cmd_ping import open_cmd_ping
from .security import (
    hash_password, verify_password, ensure_default_admin, log_action,
    get_current_user, get_current_user_optional, require_admin,
    require_operator_or_admin, require_any, ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY,
)

app = FastAPI(title="Ping Monitor v4 — Sotreq CAT")

# Chave de sessão persistente (para não deslogar todo mundo a cada reinício)
SECRET_KEY_FILE = os.path.join(data_dir(), ".secret_key")


def _get_or_create_secret_key() -> str:
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(SECRET_KEY_FILE, "w") as f:
        f.write(key)
    return key


app.add_middleware(SessionMiddleware, secret_key=_get_or_create_secret_key(), same_site="lax")


class LoginIn(BaseModel):
    username: str
    password: str


class UserIn(BaseModel):
    username: str
    password: str
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    active: bool

    class Config:
        from_attributes = True


class EquipmentAssetOut(BaseModel):
    id: int
    asset_type: str
    asset_label: str
    display_model: str | None
    ip: str | None
    last_status: bool | None
    last_rtt_ms: float | None
    last_checked: str | None
    consecutive_failures: int

    class Config:
        from_attributes = True


class EquipmentOut(BaseModel):
    id: int
    tag: str
    model: str
    machine_type: str
    icon: str
    active: bool
    assets: list[EquipmentAssetOut]

    class Config:
        from_attributes = True


@app.on_event("startup")
async def startup():
    init_db()
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()
    # IMPORTANTE: o monitoramento NÃO inicia sozinho. Só quando o usuário
    # apertar o botão de play no painel.


# ---------- Autenticação ----------

@app.post("/api/login")
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not user.active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Usuário ou senha inválidos")
    request.session["user_id"] = user.id
    log_action(db, user.username, "login")
    return {"id": user.id, "username": user.username, "role": user.role}


@app.post("/api/logout")
def logout(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    log_action(db, user.username, "logout")
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
def me(user: User | None = Depends(get_current_user_optional)):
    if not user:
        raise HTTPException(401, "Não autenticado")
    return {"id": user.id, "username": user.username, "role": user.role}


# ---------- Gestão de usuários (admin) ----------

@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.username).all()


@app.post("/api/users", response_model=UserOut)
def create_user(data: UserIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if data.role not in (ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY):
        raise HTTPException(400, "Perfil inválido")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Já existe um usuário com esse nome")
    user = User(username=data.username, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, admin.username, "criar_usuario", f"{data.username} ({data.role})")
    return user


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    if user.id == admin.id:
        raise HTTPException(400, "Você não pode remover seu próprio usuário")
    db.delete(user)
    db.commit()
    log_action(db, admin.username, "remover_usuario", user.username)
    return {"ok": True}


@app.get("/api/audit-log")
def audit_log(limit: int = 200, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "timestamp": to_brasilia(r.timestamp).isoformat(),
            "username": r.username,
            "action": r.action,
            "details": r.details,
        }
        for r in rows
    ]


# ---------- WebSocket (exige sessão válida) ----------

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    user_id = websocket.session.get("user_id") if hasattr(websocket, "session") else None
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------- Controle do monitoramento (play/pause/stop) ----------

@app.post("/api/monitoring/start")
async def monitoring_start(db: Session = Depends(get_db), user: User = Depends(require_operator_or_admin)):
    started = controller.start()
    if started:
        log_action(db, user.username, "iniciar_monitoramento")
    return {"running": controller.running}


@app.post("/api/monitoring/stop")
async def monitoring_stop(db: Session = Depends(get_db), user: User = Depends(require_operator_or_admin)):
    stopped = controller.stop()
    if stopped:
        log_action(db, user.username, "pausar_monitoramento")
    return {"running": controller.running}


@app.get("/api/monitoring/status")
def monitoring_status(_: User = Depends(require_any)):
    return {"running": controller.running, "cycle_seconds": CYCLE_SECONDS}


# ---------- Equipamentos e ativos ----------

def _serialize_equipment(eq: Equipment) -> dict:
    return {
        "id": eq.id,
        "tag": eq.tag,
        "model": eq.model,
        "machine_type": eq.machine_type,
        "icon": eq.icon,
        "active": eq.active,
        "assets": [
            {
                "id": a.id,
                "asset_type": a.asset_type,
                "asset_label": ASSET_TYPE_LABELS.get(a.asset_type, a.asset_type),
                "display_model": a.display_model,
                "ip": a.ip,
                "last_status": a.last_status,
                "last_rtt_ms": a.last_rtt_ms,
                "last_checked": to_brasilia(a.last_checked).isoformat() if a.last_checked else None,
                "consecutive_failures": a.consecutive_failures,
            }
            for a in eq.assets
        ],
    }


@app.get("/api/equipment")
def list_equipment(db: Session = Depends(get_db), _: User = Depends(require_any)):
    eqs = db.query(Equipment).options(joinedload(Equipment.assets)).order_by(Equipment.tag).all()
    return [_serialize_equipment(e) for e in eqs]


class AssetUpdateIn(BaseModel):
    ip: str | None = None
    display_model: str | None = None
    active: bool = True


@app.put("/api/assets/{asset_id}")
def update_asset(
    asset_id: int, data: AssetUpdateIn, db: Session = Depends(get_db),
    user: User = Depends(require_operator_or_admin),
):
    asset = db.query(Asset).get(asset_id)
    if not asset:
        raise HTTPException(404, "Ativo não encontrado")
    asset.ip = data.ip
    asset.display_model = data.display_model
    asset.active = data.active
    db.commit()
    log_action(db, user.username, "editar_ativo", f"{asset.equipment.tag} / {asset.asset_type}")
    return {"ok": True}


@app.post("/api/import-excel")
async def import_excel(
    file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_operator_or_admin),
):
    content = await file.read()
    try:
        summary = import_equipment_from_excel(db, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    log_action(db, user.username, "importar_planilha", str(summary))
    return summary


# ---------- Ping pontual / contínuo via CMD (aba 1) ----------

class CmdPingIn(BaseModel):
    ip: str
    continuous: bool = False


@app.post("/api/cmd-ping")
def cmd_ping(data: CmdPingIn, db: Session = Depends(get_db), user: User = Depends(require_any)):
    result = open_cmd_ping(data.ip, data.continuous)
    log_action(db, user.username, "ping_pontual", f"{data.ip} (contínuo={data.continuous})")
    return result


# ---------- Histórico / gráfico ----------

@app.get("/api/history/{asset_id}")
def asset_history(asset_id: int, hours: int = 24, db: Session = Depends(get_db), _: User = Depends(require_any)):
    since = now_utc() - timedelta(hours=hours)
    rows = (
        db.query(PingResult)
        .filter(PingResult.asset_id == asset_id, PingResult.timestamp >= since)
        .order_by(PingResult.timestamp)
        .all()
    )
    return [
        {
            "timestamp": to_brasilia(r.timestamp).isoformat(),
            "is_alive": r.is_alive,
            "rtt_ms": r.rtt_ms,
        }
        for r in rows
    ]


# ---------- Exportação de relatório ----------

@app.get("/api/export")
def export_report(hours: int = 24, db: Session = Depends(get_db), _: User = Depends(require_any)):
    since = now_utc() - timedelta(hours=hours)
    equipments = db.query(Equipment).options(joinedload(Equipment.assets)).all()
    rows = []
    for eq in equipments:
        for a in eq.assets:
            history = (
                db.query(PingResult)
                .filter(PingResult.asset_id == a.id, PingResult.timestamp >= since)
                .all()
            )
            total = len(history)
            online = sum(1 for h in history if h.is_alive)
            uptime = round((online / total) * 100, 1) if total else None
            avg_rtt = (
                round(sum(h.rtt_ms for h in history if h.rtt_ms) / max(online, 1), 1)
                if online else None
            )
            rows.append({
                "Equipamento": eq.tag,
                "Modelo": eq.model,
                "Tipo": eq.machine_type,
                "Ativo": ASSET_TYPE_LABELS.get(a.asset_type, a.asset_type),
                "IP": a.ip,
                "Status Atual": "Online" if a.last_status else "Offline" if a.last_status is not None else "Desconhecido",
                f"Uptime {hours}h (%)": uptime,
                "RTT Médio (ms)": avg_rtt,
                "Falhas Consecutivas": a.consecutive_failures,
                "Última Verificação": to_brasilia(a.last_checked) if a.last_checked else None,
            })

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatorio")
    buffer.seek(0)

    filename = f"relatorio_ping_{to_brasilia(now_utc()).strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------- Frontend ----------

app.mount("/static", StaticFiles(directory=static_dir()), name="static")


@app.get("/")
def index(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")
    return FileResponse(os.path.join(static_dir(), "index.html"))


@app.get("/login")
def login_page():
    return FileResponse(os.path.join(static_dir(), "login.html"))
