import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import settings


def _build_engine():
    runtime_database_url = os.getenv("KCE_RUNTIME_DATABASE_URL", settings.database_url)
    connect_args = {"check_same_thread": False} if runtime_database_url.startswith("sqlite") else {}
    return create_engine(runtime_database_url, future=True, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


def get_db_session():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
