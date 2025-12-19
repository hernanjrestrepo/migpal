#!/usr/bin/env python3
import os, sys, json, subprocess
from pathlib import Path

ROOT = Path("/workspace/migpal").resolve()
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"

def sh(cmd: str, check=True):
    print(f"\n$ {cmd}")
    p = subprocess.run(cmd, shell=True, executable="/bin/bash",
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(p.stdout.rstrip())
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode, p.stdout

def file_exists(p: Path):
    return "OK" if p.exists() else "MISSING"

def main():
    print("=== MigPAL Audit CLI ===")
    print("Root:", ROOT)

    # 1) Estructura mínima
    must = [
        ROOT/"GEMINI.md", ROOT/"README.md",
        ROOT/"docs"/"ARCHITECTURE.md", ROOT/"docs"/"PORTS.md",
        SCRIPTS/"start_all.sh", SCRIPTS/"stop_all.sh", SCRIPTS/"healthcheck.sh",
        BACKEND/"main.py", BACKEND/"app",
        BACKEND/"alembic.ini", BACKEND/"alembic"/"env.py",
    ]
    print("\n[FILES]")
    for p in must:
        print(f"- {p.relative_to(ROOT)}: {file_exists(p)}")

    # 2) Puertos típicos: mostrar ocupados (sin matar nada)
    sh(r"""ss -lntp | egrep ":8000|:8001|:8002|:8010|:8011|:8012|:8020|:8021|:8030|:8031|:8032|:8033|:8034|:5432" || true""", check=False)

    # 3) Validar que scripts existen (evita el error “No such file or directory”)
    if not (SCRIPTS/"healthcheck.sh").exists():
        print("\n[ERROR] Falta scripts/healthcheck.sh. Revisa checkout/paths.")
        return 2

    # 4) Diagnóstico Alembic/SQLModel metadata
    print("\n[ALEMBIC/DB] metadata.tables keys")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)  # para importar app.*
    code = r"""
import os
from pathlib import Path
print("PYTHONPATH=", os.environ.get("PYTHONPATH"))
try:
    from app.db.base import metadata
    print("metadata type:", type(metadata))
    print("tables:", list(getattr(metadata, "tables", {}).keys()))
except Exception as e:
    print("FAIL importing app.db.base.metadata:", repr(e))

try:
    from sqlmodel import SQLModel
    print("SQLModel tables:", list(SQLModel.metadata.tables.keys()))
except Exception as e:
    print("FAIL importing SQLModel:", repr(e))
"""
    sh(f"""cd {BACKEND} && . .venv/bin/activate && python - <<'PY'\n{code}\nPY""", check=False)

    # 5) Ver qué está apuntando Alembic
    sh(f"""cd {BACKEND} && . .venv/bin/activate && grep -n "sqlalchemy.url" alembic.ini || true""", check=False)

    # 6) Mostrar pista de por qué solo crea alembic_version
    print("\n[LIKELY CAUSE]")
    print("- Si metadata.tables sale vacío: tus modelos NO se están importando al cargar app.db.base, o target_metadata apunta a la metadata incorrecta.")
    print("- Solución típica: app/db/base.py debe importar los modelos (para registrarlos) y exponer metadata = SQLModel.metadata.")
    print("- Alternativa: en alembic/env.py usar target_metadata = SQLModel.metadata y asegurar sys.path/PYTHONPATH.")

    # 7) Checklist de validación sin romper otros proyectos
    print("\n[CHECKLIST]")
    print("1) ./cli.py  (levanta backend en puerto libre y healthcheck OK)")
    print("2) BASE_URL=http://127.0.0.1:<PUERTO> ./scripts/healthcheck.sh")
    print("3) cd backend && . .venv/bin/activate && alembic current && alembic history")
    print("4) cd backend && python -c \"from app.db.base import metadata; print(list(metadata.tables.keys()))\"")
    print("5) psql: sudo -u postgres psql -d migpal -c \"\\dt\"")

if __name__ == "__main__":
    main()
