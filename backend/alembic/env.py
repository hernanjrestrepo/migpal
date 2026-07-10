from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# --- asegurar imports correctos del proyecto ---
BASE_DIR = Path(__file__).resolve().parents[1]  # /workspace/migpal/backend
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Foundation: DATABASE_URL del entorno tiene prioridad sobre alembic.ini,
#     para que el mismo alembic.ini sirva tanto para SQLite local como para
#     Postgres en Docker Compose sin editar el archivo. ---
_env_db_url = os.getenv("DATABASE_URL")
if _env_db_url:
    config.set_main_option("sqlalchemy.url", _env_db_url)

# --- IMPORTANTE: importar TODOS los modelos (app/db/base.py es la fuente
#     única de verdad de qué tablas existen) para que autogenerate y
#     upgrade/downgrade operen sobre el esquema completo, no un subconjunto. ---
from app.db.base import metadata as target_metadata  # noqa: E402


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
