import os
from sqlmodel import SQLModel, create_engine, Session

# The database file will be `migpal.db` in the `backend` directory.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////workspace/migpal/backend/migpal.db")

# The `connect_args` are needed only for SQLite
connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

# This function is kept for now, as it might be useful for quick dev setups,
# but for production and testing, Alembic is the source of truth.
def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
