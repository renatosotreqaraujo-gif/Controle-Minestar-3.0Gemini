"""
Monitoramento contínuo controlado manualmente (play/pause/stop).

Diferente da v3, o monitoramento NÃO inicia sozinho quando o servidor sobe.
Ele só começa quando alguém aperta "play" no painel, e para quando alguém
aperta "pausar/parar". Enquanto pausado, os últimos status ficam congelados
na tela (não zeramos nada).
"""
import asyncio
from datetime import datetime

from .database import SessionLocal, Asset, PingResult
from .ping_service import ping_batch
from .ws_manager import manager
from .timezone_utils import now_utc

CYCLE_SECONDS = 30
FAILURE_THRESHOLD = 2


class MonitoringController:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self.running = False

    def start(self):
        if self.running:
            return False
        self.running = True
        self._task = asyncio.create_task(self._loop())
        return True

    def stop(self):
        if not self.running:
            return False
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        return True

    async def _loop(self):
        try:
            while self.running:
                await self._run_cycle()
                await asyncio.sleep(CYCLE_SECONDS)
        except asyncio.CancelledError:
            pass

    async def _run_cycle(self):
        db = SessionLocal()
        try:
            assets = (
                db.query(Asset)
                .filter(Asset.active == True, Asset.ip.isnot(None))  # noqa: E712
                .all()
            )
            if not assets:
                return

            ip_list = [a.ip for a in assets]
            results = await ping_batch(ip_list)
            now = now_utc()
            went_down = []

            for asset in assets:
                r = results.get(asset.ip)
                if not r:
                    continue

                is_alive = r["is_alive"]
                was_alive = asset.last_status

                asset.consecutive_failures = 0 if is_alive else (asset.consecutive_failures or 0) + 1

                if asset.consecutive_failures == FAILURE_THRESHOLD and (was_alive is None or was_alive):
                    went_down.append({
                        "id": asset.id,
                        "equipment_tag": asset.equipment.tag,
                        "asset_type": asset.asset_type,
                        "ip": asset.ip,
                    })

                asset.last_status = is_alive
                asset.last_rtt_ms = r["rtt_ms"]
                asset.last_checked = now

                db.add(PingResult(
                    asset_id=asset.id, timestamp=now, is_alive=is_alive,
                    rtt_ms=r["rtt_ms"], packet_loss=r["packet_loss"],
                ))

            db.commit()

            payload = {
                "type": "status_update",
                "timestamp": now.isoformat(),
                "assets": [
                    {
                        "id": a.id,
                        "equipment_id": a.equipment_id,
                        "asset_type": a.asset_type,
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


controller = MonitoringController()
