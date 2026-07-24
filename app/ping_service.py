"""
Serviço de ping.

Diferente da v2.0 (que abria o CMD e rodava `ping` um por um),
aqui usamos icmplib para mandar ICMP echo direto, de forma
assíncrona e em paralelo, com um limite de concorrência para
não estourar a rede quando tivermos 200+ ativos.
"""
import asyncio
from icmplib import async_ping

# Limite de pings simultâneos. Com 200+ ativos, sem limite o SO
# pode reclamar de "too many open sockets" e a rede pode saturar.
# 40-60 é um bom equilíbrio entre velocidade e segurança.
MAX_CONCURRENT_PINGS = 40

# Configurações do ping (ajustáveis conforme a rede)
PING_COUNT = 2          # pacotes por tentativa
PING_TIMEOUT = 1.5       # segundos por pacote
PING_INTERVAL = 0.2      # intervalo entre pacotes


async def ping_one(ip: str) -> dict:
    """Pinga um único IP e retorna um resumo do resultado."""
    try:
        host = await async_ping(
            ip,
            count=PING_COUNT,
            timeout=PING_TIMEOUT,
            interval=PING_INTERVAL,
            privileged=False,  # não exige admin/root para rodar
        )
        return {
            "ip": ip,
            "is_alive": host.is_alive,
            "rtt_ms": round(host.avg_rtt, 1) if host.is_alive else None,
            "packet_loss": round(host.packet_loss, 2),
        }
    except Exception:
        return {"ip": ip, "is_alive": False, "rtt_ms": None, "packet_loss": 1.0}


async def ping_batch(ips: list[str]) -> dict[str, dict]:
    """
    Pinga uma lista de IPs em paralelo, respeitando o limite de
    concorrência. Retorna um dict indexado por IP.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)

    async def _bounded(ip: str):
        async with semaphore:
            return await ping_one(ip)

    results = await asyncio.gather(*(_bounded(ip) for ip in ips))
    return {r["ip"]: r for r in results}
