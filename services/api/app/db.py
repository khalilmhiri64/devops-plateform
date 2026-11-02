"""Database engine / session management."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker | None = None


def init_engine(url: str):
    global _engine, _SessionLocal
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    _engine = create_engine(url, **kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    from . import models  # noqa: F401  (register tables)

    Base.metadata.create_all(_engine)
    return _engine


def get_engine():
    return _engine


def get_session() -> Iterator[Session]:
    assert _SessionLocal is not None, "init_engine() must be called first"
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
