"""
Ponto de entrada do Ping Monitor.

Este arquivo é o que o PyInstaller transforma em .exe. Ele:
  1. Sobe o servidor web (uvicorn) na porta 8000.
  2. Abre o navegador automaticamente em http://localhost:8000.
  3. Mostra uma janela de console simples — feche essa janela (ou
     pressione Ctrl+C) para parar o monitoramento.
"""
import sys
import threading
import time
import webbrowser

import uvicorn

PORT = 8000


def open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass  # se não conseguir abrir sozinho, o usuário acessa manualmente


def main():
    # Import direto do objeto app (em vez de string "app.main:app") para
    # evitar problemas de import dinâmico dentro do executável empacotado.
    from app.main import app

    print("=" * 56)
    print("  PING MONITOR")
    print(f"  Painel disponível em: http://localhost:{PORT}")
    print("  Outros PCs da rede acessam via http://<IP-DESTE-PC>:8000")
    print("  Não feche esta janela enquanto quiser usar o painel.")
    print("=" * 56)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
