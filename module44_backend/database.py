"""SQLAlchemy session factory for Module 4.4 using the main app DB settings."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from module44_backend.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
