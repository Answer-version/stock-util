from __future__ import annotations

import os
import queue
import socket
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

from streamlit.web import bootstrap

from quantvibe.core.paths import ensure_runtime_layout, local_config_path, resource_path, runtime_root


WINDOW_TITLE = "QuantVibe 中文因子面板"
WINDOW_SIZE = (1480, 980)
HEALTHCHECK_TIMEOUT_SECONDS = 45


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _healthcheck_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/_stcore/health"


def _streamlit_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/"


def _streamlit_flags(port: int) -> dict[str, object]:
    return {
        "server.headless": True,
        "server.address": "127.0.0.1",
        "server.port": port,
        "browser.gatherUsageStats": False,
        "server.fileWatcherType": "none",
        "client.toolbarMode": "minimal",
    }


def _bootstrap_server(port: int, errors: queue.Queue[BaseException]) -> None:
    script_path = resource_path("streamlit_app.py")
    if not script_path.exists():
        errors.put(FileNotFoundError(f"streamlit app not found: {script_path}"))
        return
    try:
        bootstrap.run(
            str(script_path),
            False,
            [],
            _streamlit_flags(port),
        )
    except BaseException as exc:  # pragma: no cover - surfaced in startup wait
        errors.put(exc)


def _wait_for_server(port: int, worker: threading.Thread, errors: queue.Queue[BaseException]) -> None:
    deadline = time.monotonic() + HEALTHCHECK_TIMEOUT_SECONDS
    url = _healthcheck_url(port)
    while time.monotonic() < deadline:
        if not worker.is_alive():
            try:
                raise RuntimeError("streamlit server stopped during startup") from errors.get_nowait()
            except queue.Empty as exc:
                raise RuntimeError("streamlit server stopped during startup") from exc
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except URLError:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"streamlit server failed to start within {HEALTHCHECK_TIMEOUT_SECONDS} seconds")


def _set_runtime_environment() -> None:
    ensure_runtime_layout()
    os.environ.setdefault("QUANTVIBE_RUNTIME_DIR", str(runtime_root()))
    os.environ.setdefault("QUANTVIBE_LOCAL_CONFIG", str(local_config_path()))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")


def main() -> None:
    _set_runtime_environment()

    try:
        import webview
    except ImportError as exc:  # pragma: no cover - desktop runtime only
        raise SystemExit("桌面版依赖 pywebview，请安装 requirements-desktop.txt。") from exc

    port = _find_free_port()
    errors: queue.Queue[BaseException] = queue.Queue()
    worker = threading.Thread(
        target=_bootstrap_server,
        args=(port, errors),
        name="quantvibe-streamlit",
        daemon=True,
    )
    worker.start()
    _wait_for_server(port, worker, errors)

    webview.create_window(
        WINDOW_TITLE,
        _streamlit_url(port),
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=(1180, 760),
    )
    webview.start()


if __name__ == "__main__":
    main()
