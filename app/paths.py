"""
Resolução de caminhos que funciona nos dois cenários:

1. Rodando normalmente com `python`/`uvicorn` (modo desenvolvimento).
2. Rodando empacotado como .exe via PyInstaller (modo instalado no PC do usuário).

Regra importante: arquivos "embutidos" no .exe (como o index.html) ficam numa
pasta temporária que o PyInstaller apaga ao fechar o programa — então NUNCA
salvamos dados ali. O banco de dados (ping_tool.db) sempre fica ao lado do
.exe (ou do projeto, em modo desenvolvimento), para persistir entre execuções.
"""
import os
import sys


def is_frozen() -> bool:
    """True quando rodando como .exe empacotado pelo PyInstaller."""
    return getattr(sys, "frozen", False)


def bundle_dir() -> str:
    """
    Onde estão os arquivos do próprio app (código, templates estáticos).
    No .exe, isso é a pasta temporária de extração do PyInstaller.
    """
    if is_frozen():
        return sys._MEIPASS  # type: ignore[attr-defined]
    # raiz do projeto (uma pasta acima de app/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    """
    Onde salvar dados persistentes (banco de dados, relatórios).
    No .exe, é a pasta onde o .exe está instalado — não a pasta temporária.
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def static_dir() -> str:
    return os.path.join(bundle_dir(), "app", "static")
