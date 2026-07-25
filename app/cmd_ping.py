"""
Teste de ping "manual", abrindo o CMD — igual ao comportamento da v2.0,
só que agora acionado a partir do painel web (você escolhe o equipamento
e o ativo, e o sistema abre uma janela de CMD já rodando o ping).

Só funciona quando o servidor roda no próprio Windows onde o CMD deve
abrir (é exatamente o caso do PingMonitor.exe rodando localmente).
"""
import platform
import subprocess


def open_cmd_ping(ip: str, continuous: bool) -> dict:
    system = platform.system()

    if system == "Windows":
        if continuous:
            # -t = ping contínuo (até fechar a janela ou Ctrl+C)
            cmd = f'start "Ping {ip}" cmd /k ping {ip} -t'
        else:
            # -n 4 = 4 pacotes e encerra, mas deixa a janela aberta pra ler o resultado
            cmd = f'start "Ping {ip}" cmd /k ping {ip} -n 4'
        subprocess.Popen(cmd, shell=True)
        return {"opened": True, "mode": "cmd"}

    # Fallback para desenvolvimento/testes fora do Windows: roda em background
    # e não abre janela (não existe CMD fora do Windows).
    count_flag = "-t" if continuous else "-c 4"
    try:
        subprocess.Popen(f"ping {count_flag} {ip}", shell=True)
        return {"opened": True, "mode": "background", "note": "CMD só abre no Windows"}
    except Exception as e:
        return {"opened": False, "error": str(e)}
