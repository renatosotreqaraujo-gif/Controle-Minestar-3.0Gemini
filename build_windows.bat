@echo off
REM ============================================================
REM  Ping Monitor - Build do executavel (.exe)
REM
REM  Rode este arquivo UMA VEZ, numa maquina Windows que tenha
REM  Python instalado. Ele gera um PingMonitor.exe dentro da
REM  pasta "dist", que pode ser copiado para qualquer outro PC
REM  Windows SEM precisar instalar Python la.
REM ============================================================

cd /d %~dp0

echo.
echo [1/3] Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Gerando o executavel (isso pode levar alguns minutos)...
pyinstaller --onefile --name PingMonitor ^
  --add-data "app/static;app/static" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols ^
  --hidden-import uvicorn.protocols.http ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan ^
  --hidden-import uvicorn.lifespan.on ^
  --hidden-import passlib.handlers.bcrypt ^
  --collect-submodules passlib ^
  run.py

echo.
echo [3/3] Pronto!
echo O executavel esta em: dist\PingMonitor.exe
echo.
echo Copie o arquivo dist\PingMonitor.exe para qualquer PC Windows
echo e de dois cliques para rodar - nao precisa instalar nada la.
echo.
pause
