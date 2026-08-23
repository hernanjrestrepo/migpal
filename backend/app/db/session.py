import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# Load backend-specific .env (preferred) and fall back to project root
backend_root = Path(__file__).resolve().parents[2]
backend_env = backend_root / ".env"
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env, override=True)
else:
    # fallback to repository root .env if backend env missing
    repo_root_env = backend_root.parent / ".env"
    if repo_root_env.exists():
        load_dotenv(dotenv_path=repo_root_env, override=True)

# The database file will be `migpal.db` in the `backend` directory.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./migpal.db")

# The `connect_args` are needed only for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


# This function is kept for now, as it might be useful for quick dev setups,
# but for production and testing, Alembic is the source of truth.
def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
