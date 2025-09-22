from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite file in the project root; echo=False to keep logs quiet.
ENGINE = create_engine("sqlite:///habits.db", echo=False, future=True)

class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy models."""
    pass


SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)

def create_schema() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=ENGINE)


