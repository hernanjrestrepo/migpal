#!/usr/bin/env python3
import os
import subprocess
import socket

BASE_DIR = "/workspace/migpal"
BACKEND_DIR = f"{BASE_DIR}/backend"

def sh(cmd: str):
    cmd = cmd.strip() + "\n"
    print(f"▶ {cmd}")
    subprocess.check_call(cmd, shell=True, executable="/bin/bash")

def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0

def find_port(start=8031, end=8099) -> int:
    for p in range(start, end):
        if port_free(p):
            return p
    raise RuntimeError("No hay puertos libres entre 8031 y 8099")

def ensure_db():
    sh(r"""
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='migpal'" | grep -q 1 \
|| sudo -u postgres psql -c "CREATE USER migpal WITH PASSWORD 'migpal';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='migpal'" | grep -q 1 \
|| sudo -u postgres psql -c "CREATE DATABASE migpal OWNER migpal;"
""")

def migrate():
    sh(f"""
cd {BACKEND_DIR}
source .venv/bin/activate
alembic upgrade head
""")

def start_backend():
    port = find_port()
    os.environ["MIGPAL_BACKEND_PORT"] = str(port)

    sh(f"""
cd {BASE_DIR}
./scripts/start_all.sh
""")

    sh(f"""
cd {BASE_DIR}
BASE_URL=http://127.0.0.1:{port} ./scripts/healthcheck.sh
""")

if __name__ == "__main__":
    ensure_db()
    migrate()
    start_backend()
    print("✅ MigPAL listo. Todo automático.")
