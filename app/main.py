import asyncio
import io
import os
from datetime import datetime, timedelta

import pandas as pd
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import init_db, get_db, SessionLocal, Asset, PingResult
from .ping_service import ping_batch
from .ws_manager import manager
from .excel_import import import_assets_from_excel
from .paths import static_dir

app = FastAPI(title="Ping Monitor v3")

# Ciclo do scheduler (segundos entre rodadas de ping)
CYCLE_SECONDS = 30
# Quantas falhas seguidas até considerar "queda confirmada" (evita alarme falso)
FAILURE_THRESHOLD = 2


class AssetIn(BaseModel):
    name: str
    ip: str
    group: str = "Geral"
    active: bool = True


class AssetOut(AssetIn):
    id: int
    last_status: bool | None = None
    last_rtt_ms: float | None = None
    last_checked: datetime | None = None
    consecutive_failures: int = 0

    class Config:
        from_attributes = True


@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(ping_loop())


# ---------- WebSocket (painel em tempo real) ----------

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantém viva, não esperamos nada do cliente
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------- Loop de ping em background ----------

async def ping_loop():
    while True:
        db: Session = SessionLocal()
        try:
            assets = db.query(Asset).filter(Asset.active == True).all()  # noqa: E712
            if assets:
                ip_list = [a.ip for a in assets]
                results = await ping_batch(ip_list)
                now = datetime.utcnow()
                went_down = []

                for asset in assets:
                    r = results.get(asset.ip)
                    if not r:
                        continue

                    is_alive = r["is_alive"]
                    was_alive = asset.last_status

                    if is_alive:
                        asset.consecutive_failures = 0
                    else:
                        asset.consecutive_failures = (asset.consecutive_failures or 0) + 1

                    # Só disparamos alerta de "queda" quando cruza o threshold
                    if (
                        asset.consecutive_failures == FAILURE_THRESHOLD
                        and (was_alive is None or was_alive)
                    ):
                        went_down.append({"id": asset.id, "name": asset.name, "ip": asset.ip})

                    asset.last_status = is_alive
                    asset.last_rtt_ms = r["rtt_ms"]
                    asset.last_checked = now

                    db.add(PingResult(
                        asset_id=asset.id,
                        timestamp=now,
                        is_alive=is_alive,
                        rtt_ms=r["rtt_ms"],
                        packet_loss=r["packet_loss"],
                    ))

                db.commit()

                # Broadcast do estado atual de todos os ativos
                payload = {
                    "type": "status_update",
                    "timestamp": now.isoformat(),
                    "assets": [
                        {
                            "id": a.id,
                            "name": a.name,
                            "ip": a.ip,
                            "group": a.group,
                            "last_status": a.last_status,
                            "last_rtt_ms": a.last_rtt_ms,
                            "consecutive_failures": a.consecutive_failures,
                        }
                        for a in assets
                    ],
                }
                await manager.broadcast(payload)

                if went_down:
                    await manager.broadcast({"type": "alert_down", "assets": went_down})
        finally:
            db.close()

        await asyncio.sleep(CYCLE_SECONDS)


# ---------- CRUD de ativos ----------

@app.get("/api/assets", response_model=list[AssetOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).order_by(Asset.group, Asset.name).all()


@app.post("/api/assets", response_model=AssetOut)
def create_asset(asset: AssetIn, db: Session = Depends(get_db)):
    if db.query(Asset).filter(Asset.ip == asset.ip).first():
        raise HTTPException(400, "Já existe um ativo com esse IP")
    obj = Asset(**asset.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.put("/api/assets/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: int, asset: AssetIn, db: Session = Depends(get_db)):
    obj = db.query(Asset).get(asset_id)
    if not obj:
        raise HTTPException(404, "Ativo não encontrado")
    for k, v in asset.dict().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/api/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    obj = db.query(Asset).get(asset_id)
    if not obj:
        raise HTTPException(404, "Ativo não encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ---------- Importação via Excel ----------

@app.post("/api/import-excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        summary = import_assets_from_excel(db, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return summary


# ---------- Histórico / gráfico ----------

@app.get("/api/history/{asset_id}")
def asset_history(asset_id: int, hours: int = 24, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(PingResult)
        .filter(PingResult.asset_id == asset_id, PingResult.timestamp >= since)
        .order_by(PingResult.timestamp)
        .all()
    )
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "is_alive": r.is_alive,
            "rtt_ms": r.rtt_ms,
        }
        for r in rows
    ]


# ---------- Exportação de relatório ----------

@app.get("/api/export")
def export_report(hours: int = 24, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    assets = db.query(Asset).all()
    rows = []
    for a in assets:
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
            "Nome": a.name,
            "IP": a.ip,
            "Grupo": a.group,
            "Status Atual": "Online" if a.last_status else "Offline" if a.last_status is not None else "Desconhecido",
            f"Uptime {hours}h (%)": uptime,
            "RTT Médio (ms)": avg_rtt,
            "Falhas Consecutivas": a.consecutive_failures,
            "Última Verificação": a.last_checked,
        })

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatorio")
    buffer.seek(0)

    filename = f"relatorio_ping_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------- Frontend ----------

app.mount("/static", StaticFiles(directory=static_dir()), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir(), "index.html"))
