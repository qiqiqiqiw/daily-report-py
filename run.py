import sys
import os
import socket
import time
import threading
from pathlib import Path

if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
import webview
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import PORT
from app.database import SessionLocal
from app.services.report_service import auto_generate
from app.main import app as fastapi_app


def scheduled_auto_generate():
    db = SessionLocal()
    try:
        auto_generate(db)
    except Exception as e:
        print(f"定时任务执行失败: {e}")
    finally:
        db.close()


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def find_available_port(preferred_port: int, max_attempts: int = 10) -> int:
    for offset in range(max_attempts):
        port = preferred_port + offset
        if is_port_available(port):
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def run_server(port: int):
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port, reload=False)


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_auto_generate, "cron", hour=18, minute=0, id="auto_generate")

if __name__ == "__main__":
    actual_port = find_available_port(PORT)
    if actual_port != PORT:
        print(f"端口 {PORT} 已被占用，使用端口 {actual_port}")

    server_thread = threading.Thread(target=run_server, args=(actual_port,), daemon=True)
    server_thread.start()

    if not wait_for_server(actual_port):
        print("服务器启动超时")
        sys.exit(1)

    window = webview.create_window(
        "Git Daily Report",
        f"http://localhost:{actual_port}",
        width=1200,
        height=800,
        min_size=(800, 600),
    )
    webview.start()
    os._exit(0)
