import asyncio
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Garantir que a instância da aplicação FastAPI existe
app = FastAPI()

@app.websocket("/ws/instant-ping")
async def websocket_instant_ping(websocket: WebSocket):
    """
    Rota WebSocket para execução do comando PING em tempo real.
    Lê a saída do terminal do SO e transmite ao navegador,
    permitindo o encerramento do processo a qualquer momento.
    """
    await websocket.accept()
    ping_process = None

    try:
        # 1. Receber os parâmetros enviados pelo JavaScript
        data = await websocket.receive_json()
        ip = data.get("ip")
        mode = data.get("mode")  # 'pontual' ou 'continuo'

        if not ip:
            await websocket.send_text("Erro: Nenhum IP foi fornecido.")
            await websocket.close()
            return

        # 2. Definir o comando com base no SO (Windows vs Linux/Mac)
        is_windows = sys.platform.startswith("win")
        
        if is_windows:
            # No Windows: -t (contínuo), -n 4 (pontual de 4 pacotes)
            args = ["ping", ip, "-t"] if mode == "continuo" else ["ping", ip, "-n", "4"]
        else:
            # No Linux/Mac: sem parâmetro de contagem (contínuo), -c 4 (pontual)
            args = ["ping", ip] if mode == "continuo" else ["ping", ip, "-c", "4"]

        # 3. Criar o processo do PING em plano de fundo sem abrir janela CMD
        ping_process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # 4. Task assíncrona para escutar o comando "stop" vindo do botão Fechar
        async def listen_cancel():
            try:
                while True:
                    msg = await websocket.receive_json()
                    if msg.get("action") == "stop" and ping_process:
                        ping_process.kill()
                        break
            except Exception:
                pass

        cancel_task = asyncio.create_task(listen_cancel())

        # 5. Ler a saída do PING linha por linha e enviar ao navegador
        while True:
            line = await ping_process.stdout.readline()
            if not line:
                break
            
            # Decodificar texto (CP1252 no Windows para acentuação correta do CMD)
            text = line.decode('cp1252' if is_windows else 'utf-8', errors='replace')
            await websocket.send_text(text)

        cancel_task.cancel()
        await websocket.send_text("\n--- Teste Encerrado ---")

    except WebSocketDisconnect:
        # Se o utilizador fechar a página/aba, garante a eliminação do processo
        if ping_process:
            ping_process.kill()
    except Exception as e:
        await websocket.send_text(f"\nErro no processamento: {str(e)}")
    finally:
        # Garantia final de liberação do processo do sistema
        if ping_process and ping_process.returncode is None:
            try:
                ping_process.kill()
            except ProcessLookupError:
                pass
        
        try:
            await websocket.close()
        except Exception:
            pass
