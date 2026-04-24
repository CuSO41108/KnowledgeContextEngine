from __future__ import annotations

from typing import Any

from app.settings import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except ModuleNotFoundError:
    class _PlaceholderEngine:
        def __init__(self, url: str, *, future: bool) -> None:
            self.url = url
            self.future = future

    class _PlaceholderSession:
        def __init__(self, bind: Any, autoflush: bool, autocommit: bool) -> None:
            self.bind = bind
            self.autoflush = autoflush
            self.autocommit = autocommit

    class _SessionFactory:
        def __init__(self, bind: Any, autoflush: bool, autocommit: bool) -> None:
            self.bind = bind
            self.autoflush = autoflush
            self.autocommit = autocommit

        def __call__(self) -> _PlaceholderSession:
            return _PlaceholderSession(
                bind=self.bind,
                autoflush=self.autoflush,
                autocommit=self.autocommit,
            )

    class _PlaceholderMetadata:
        def __init__(self) -> None:
            self.tables: dict[str, object] = {}

    class _PlaceholderBase:
        metadata = _PlaceholderMetadata()

    def create_engine(url: str, *, future: bool = True) -> _PlaceholderEngine:
        return _PlaceholderEngine(url=url, future=future)

    def sessionmaker(*, bind: Any, autoflush: bool, autocommit: bool) -> _SessionFactory:
        return _SessionFactory(bind=bind, autoflush=autoflush, autocommit=autocommit)

    def declarative_base() -> type[_PlaceholderBase]:
        class Base(_PlaceholderBase):
            pass

        return Base


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
