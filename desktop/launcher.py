"""
StudySync desktop — ponto de entrada do executável.

Sobe o backend FastAPI (que também serve o build do frontend) numa thread, em
127.0.0.1, e abre a interface numa janela nativa do `pywebview` (WebView2 no
Windows, sem Chromium embutido). Fechar a janela encerra o servidor.

Todos os dados ficam na máquina do usuário, em `%LOCALAPPDATA%\\StudySync`:
    studysync.db   banco SQLite (migrado no boot pelo Alembic)
    secret.key     chave dos JWTs, gerada na primeira execução
    webview/       perfil do WebView2 (localStorage: sessão e tema)
    studysync.log  log do servidor

Não há tela de login: a janela pede a sessão do usuário local à `DesktopBridge`.

Uso a partir do código-fonte (sem empacotar), com o frontend já buildado:
    backend\\venv\\Scripts\\python.exe desktop\\launcher.py
"""

from __future__ import annotations

import ctypes
import logging
import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path

APP_NAME = "StudySync"
HOST = "127.0.0.1"
# Porta fixa de propósito: o localStorage do WebView2 é separado por origem, e
# uma porta nova a cada execução deslogaria o usuário e esqueceria o tema.
PREFERRED_PORT = 8765
STARTUP_TIMEOUT_SECONDS = 60
LOG_MAX_BYTES = 5 * 1024 * 1024

FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    BUNDLE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    FRONTEND_DIST = BUNDLE_DIR / "frontend_dist"
else:
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"
    sys.path.insert(0, str(PROJECT_DIR / "backend"))


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def show_error(message: str) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)  # MB_ICONERROR


def acquire_single_instance() -> object | None:
    """
    Impede duas cópias abertas ao mesmo tempo: cada uma rodaria o próprio
    agendador de lembretes sobre o mesmo banco.
    """
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, "Local\\StudySync.Desktop")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return handle


def redirect_output(log_path: Path) -> None:
    """
    No executável sem console `sys.stdout`/`sys.stderr` são `None`, e o logging
    do uvicorn e da aplicação quebraria ao escrever neles.
    """
    if log_path.exists() and log_path.stat().st_size > LOG_MAX_BYTES:
        log_path.unlink()
    stream = open(log_path, "a", encoding="utf-8", buffering=1)  # noqa: SIM115
    if sys.stdout is None or FROZEN:
        sys.stdout = stream
    if sys.stderr is None or FROZEN:
        sys.stderr = stream


def load_secret_key(path: Path) -> str:
    """Chave persistente: sem ela, reabrir o app invalidaria a sessão salva."""
    if path.exists():
        key = path.read_text(encoding="utf-8").strip()
        if key:
            return key
    key = secrets.token_urlsafe(64)
    path.write_text(key, encoding="utf-8")
    return key


def pick_port() -> int:
    for port in (PREFERRED_PORT, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return sock.getsockname()[1]
    raise RuntimeError("Nenhuma porta local disponível.")


def configure_environment(data: Path, port: int) -> None:
    """Precisa rodar antes de qualquer import de `app` (as settings são lidas no import)."""
    os.environ.update(
        {
            "ENV": "production",
            "SECRET_KEY": load_secret_key(data / "secret.key"),
            "DATABASE_URL": f"sqlite:///{(data / 'studysync.db').as_posix()}",
            "FRONTEND_DIST": str(FRONTEND_DIST),
            "BACKEND_CORS_ORIGINS": f"http://{HOST}:{port}",
        }
    )


class DesktopBridge:
    """
    Exposta à janela como `window.pywebview.api`. Só o código carregado dentro
    da janela alcança a ponte — um site aberto no navegador da máquina, ou
    outro programa chamando 127.0.0.1:8765, não recebe token e a API continua
    fechada para ele.
    """

    def local_session(self, timezone_name: str | None = None) -> dict:
        from app.services.sessions import issue_local_session

        return issue_local_session(timezone_name)


def allow_notification_permission(window, origin: str) -> None:
    """
    Libera as notificações do sistema para a interface do app.

    Sem isso o WebView2 responde `denied` a `Notification.requestPermission()`
    na hora, sem perguntar nada (o pywebview não trata `PermissionRequested`),
    e grava o `denied` no perfil — builds anteriores deixaram esse estado
    salvo, e ele não sai sozinho. Como é um app desktop, as notificações já
    abrem liberadas; quem quiser desligar usa Configurações → Notificações do
    Windows. Só notificações são tocadas: as demais permissões seguem o padrão.
    """
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2PermissionKind,
        CoreWebView2PermissionState,
    )
    from System import Func, Type

    notifications = CoreWebView2PermissionKind.Notifications
    allow = CoreWebView2PermissionState.Allow

    def on_permission_requested(_sender, args) -> None:
        # Cobre um pedido feito antes de o estado abaixo terminar de gravar.
        if args.PermissionKind == notifications:
            args.State = allow
            args.SavesInProfile = True

    def attach() -> None:
        core = window.native.browser.webview.CoreWebView2
        core.PermissionRequested += on_permission_requested
        # Sobrescreve inclusive um `denied` salvo por versões anteriores.
        core.Profile.SetPermissionStateAsync(notifications, origin, allow)

    # Objetos do WebView2 só podem ser tocados na thread da interface.
    window.native.Invoke(Func[Type](attach))


def main() -> int:
    mutex = acquire_single_instance()
    if mutex is None:
        show_error("O StudySync já está aberto.")
        return 1

    data = data_dir()
    redirect_output(data / "studysync.log")
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("studysync.desktop")

    if not (FRONTEND_DIST / "index.html").is_file():
        show_error(f"Build do frontend não encontrado em:\n{FRONTEND_DIST}")
        return 1

    port = pick_port()
    if port != PREFERRED_PORT:
        logger.warning(
            "Porta %s ocupada; usando %s (a sessão salva no app não vale nessa porta)",
            PREFERRED_PORT,
            port,
        )
    configure_environment(data, port)

    import uvicorn
    import webview

    from app.main import app

    server = uvicorn.Server(
        uvicorn.Config(app, host=HOST, port=port, log_level="warning", access_log=False)
    )
    thread = threading.Thread(target=server.run, name="uvicorn", daemon=True)
    thread.start()

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            logger.error("O servidor não iniciou")
            show_error(
                "Não foi possível iniciar o StudySync.\n\n"
                f"Detalhes em: {data / 'studysync.log'}"
            )
            return 1
        time.sleep(0.1)

    # Downloads ligados para o "Exportar agenda (.ics)"; links externos (os
    # resultados da busca de conteúdo) abrem no navegador padrão.
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True

    window = webview.create_window(
        APP_NAME,
        f"http://{HOST}:{port}/",
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#f6f1e6",  # --surface-muted, evita o flash branco
        js_api=DesktopBridge(),
    )

    # `loaded` dispara a cada navegação; o handler só precisa entrar uma vez,
    # depois que o CoreWebView2 existe.
    def on_first_load() -> None:
        window.events.loaded -= on_first_load
        try:
            allow_notification_permission(window, f"http://{HOST}:{port}")
        except Exception:
            logger.exception("Não foi possível habilitar as notificações do sistema")

    window.events.loaded += on_first_load
    webview.start(private_mode=False, storage_path=str(data / "webview"))

    # Janela fechada: encerra o servidor pelo caminho normal (lifespan desliga o agendador).
    server.should_exit = True
    thread.join(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
