"""
Internamente tudo é salvo em UTC (boa prática, evita bugs de horário de
verão / troca de servidor). Para exibição ao usuário, convertemos para
o fuso de Brasília (America/Sao_Paulo) aqui, num único lugar.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

BR_TZ = ZoneInfo("America/Sao_Paulo")
UTC = ZoneInfo("UTC")


def to_brasilia(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(BR_TZ)


def now_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)  # naive UTC, como salvamos no banco
