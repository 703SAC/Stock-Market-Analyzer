"""공용 테스트 픽스처."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import storage.models  # noqa: F401  (Base에 테이블 등록)
from storage.db import Base


@pytest.fixture
def db():
    """격리된 인메모리 SQLite 세션 (외부 API/파일 미사용)."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
