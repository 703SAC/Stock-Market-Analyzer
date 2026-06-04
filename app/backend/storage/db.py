"""SQLAlchemy database setup."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlite_url() -> str:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite:///"):
        rel = url.replace("sqlite:///", "")
        path = Path(rel)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[1] / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"
    return url


engine = create_engine(_sqlite_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from storage import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
