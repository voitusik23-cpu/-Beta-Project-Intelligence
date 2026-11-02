"""Start this app once, then open its dedicated standalone browser window."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 18762  # A previous local build is still bound to 18761 and cannot be inspected here.
URL = f"http://127.0.0.1:{PORT}"
HEALTH_URL = f"{URL}/api/health"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def health() -> dict | None:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1.2) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def port_is_open() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def open_standalone() -> None:
    chrome_paths = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    chrome = next((p for p in chrome_paths if p.is_file()), None)
    if not chrome:
        raise FileNotFoundError("Google Chrome was not found. Install Chrome to open Beta Project Intelligence.")
    subprocess.Popen([str(chrome), f"--app={URL}"])


def main() -> int:
    existing = health()
    if existing and existing.get("app") == "beta-project-intelligence":
        try:
            open_standalone()
        except FileNotFoundError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0
    if port_is_open():
        print(f"Port {PORT} belongs to a different app. It was left untouched; no page was opened.", file=sys.stderr)
        return 1

    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 6  # SW_MINIMIZE
    subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )
    for _ in range(60):
        time.sleep(0.25)
        result = health()
        if result and result.get("app") == "beta-project-intelligence":
            try:
                open_standalone()
            except FileNotFoundError as error:
                print(str(error), file=sys.stderr)
                return 1
            return 0
    print("The local server did not become ready. Check the separate server console for details.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
