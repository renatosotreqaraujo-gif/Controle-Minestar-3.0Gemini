import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- CORREÇÃO DOS IMPORTS (Suporta app/main.py e PyInstaller) ---
try:
    # Tenta importar via pacote `app`
    from app import auth, database, ping_service, ws_manager
except ModuleNotFoundError:
    # Fallback para caso esteja rodando na mesma pasta do script
    import auth
    import database
    import ping_service
    import ws_manager

# --- TRATAMENTO PARA PYINSTALLER (.EXE) ---
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Determina o diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# --- INICIALIZAÇÃO DA APLICAÇÃO FASTAPI ---
app = FastAPI(
    title="Sotreq CAT - Ping & Telemetry Monitor",
    description="Painel de Monitoramento e Diagnóstico com Suporte a CLI/CMD",
    version="3.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
@app.on_event("startup")
async def startup_db_client():
    database.init_db()

# --- ARQUIVOS ESTÁTICOS E ROTAS PRINCIPAIS ---
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    """Servidor da página principal do Dashboard (index.html)."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Arquivo index.html não encontrado em app/static/")

@app.get("/login", response_class=FileResponse)
async def serve_login():
    """Servidor da página de Login (login.html)."""
    login_path = os.path.join(STATIC_DIR, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    raise HTTPException(status_code=404, detail="Arquivo login.html não encontrado em app/static/")

# --- MODELOS DE DADOS (PYDANTIC) ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str  # admin, operator, viewer

class PingRequest(BaseModel):
    host: str

# --- ENDPOINTS DE AUTENTICAÇÃO ---
@app.post("/api/login")
async def login(data: LoginRequest):
    user = database.verify_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos."
        )
    
    token = auth.create_access_token({"sub": user["username"], "role": user["role"]})
    database.log_audit(user["username"], "LOGIN", "Usuário autenticado com sucesso")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }

@app.post("/api/logout")
async def logout(current_user: dict = Depends(auth.get_current_user)):
    database.log_audit(current_user["username"], "LOGOUT", "Sessão encerrada")
    return {"message": "Logout realizado com sucesso."}

# --- ENDPOINTS ADMINISTRATIVOS ---
@app.post("/api/users/create")
async def create_user(
    data: UserCreateRequest,
    current_user: dict = Depends(auth.require_role("admin"))
):
    success = database.create_user(data.username, data.password, data.role)
    if not success:
        raise HTTPException(status_code=400, detail="Usuário já existe.")
    
    database.log_audit(current_user["username"], "CREATE_USER", f"Criou usuário: {data.username} ({data.role})")
    return {"message": f"Usuário {data.username} criado com sucesso."}

@app.get("/api/audit-logs")
async def get_audit_logs(current_user: dict = Depends(auth.require_role("admin"))):
    return database.get_audit_logs()

# --- ENDPOINTS DE OPERAÇÃO E DIAGNÓSTICO ---
@app.post("/api/ping")
async def execute_ping(
    data: PingRequest,
    current_user: dict = Depends(auth.get_current_user)
):
    """Executa o comando de ping no backend para o terminal diagnóstico."""
    result = ping_service.run_ping(data.host)
    database.log_audit(current_user["username"], "PING_EXECUTE", f"Host testado: {data.host}")
    return result

@app.get("/api/status")
async def get_system_status():
    return {
        "status": "online",
        "version": "3.0.0-S11D",
        "active_monitors": ping_service.get_active_monitors_count()
    }

# --- WEBSOCKET PARA TELEMETRIA EM TEMPO REAL ---
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.broadcast(f"Eco: {data}")
    except Exception:
        ws_manager.disconnect(websocket)

# --- EXECUÇÃO DIRETA COM UVICORN ---
if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print(" PING MONITOR & DIAGNOSTIC SYSTEM")
    print(" Painel disponível em: http://localhost:8000")
    print(" Outros PCs da rede acessam via http://<IP-DESTE-PC>:8000")
    print(" Não feche esta janela enquanto quiser usar o painel.")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)
