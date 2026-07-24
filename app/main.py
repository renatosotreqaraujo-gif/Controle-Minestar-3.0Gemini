from fastapi import FastAPI, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import init_db, get_db_connection, log_action
from app.auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, require_roles
)

app = FastAPI()

# Inicializa o banco de dados ao subir a aplicação
init_db()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")

    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    log_action(user["username"], "LOGIN", "Usuário realizou login com sucesso")

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

@app.get("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    log_action(current_user["username"], "LOGOUT", "Usuário encerrou a sessão")
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# --- CADASTRO DE USUÁRIOS (Apenas ADMIN) ---

@app.post("/api/users/create")
async def create_user(
    new_username: str = Form(...), 
    new_password: str = Form(...), 
    role: str = Form(...),
    current_user: dict = Depends(require_roles(["admin"]))
):
    if role not in ["admin", "operator", "viewer"]:
        raise HTTPException(status_code=400, detail="Perfil inválido")

    conn = get_db_connection()
    try:
        hashed_pw = get_password_hash(new_password)
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (new_username, hashed_pw, role)
        )
        conn.commit()
        log_action(current_user["username"], "CREATE_USER", f"Criou o usuário {new_username} ({role})")
    except Exception:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    finally:
        conn.close()

    return {"message": f"Usuário {new_username} criado com sucesso!"}

# --- EXEMPLO DE ROTAS PROTEGIDAS ---

# Qualquer um logado (Admin, Operator, Viewer) pode disparar o PING
@app.post("/api/ping/test")
async def test_ping(current_user: dict = Depends(require_roles(["admin", "operator", "viewer"]))):
    log_action(current_user["username"], "PING_TEST", "Executou teste de ping")
    return {"status": "Ping executado com sucesso!"}

# Apenas Admin e Operator podem alterar/cadastrar configurações de rede
@app.post("/api/config/update")
async def update_config(current_user: dict = Depends(require_roles(["admin", "operator"]))):
    log_action(current_user["username"], "CONFIG_UPDATE", "Atualizou configurações do sistema")
    return {"status": "Configurações salvas!"}

# Rota para visualizar os logs de auditoria (Apenas Admin)
@app.get("/api/logs")
async def get_logs(current_user: dict = Depends(require_roles(["admin"]))):
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(log) for log in logs]
