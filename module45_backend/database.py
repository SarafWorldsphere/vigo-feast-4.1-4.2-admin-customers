import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.db import get_db_connection

BASE_DIR = Path(__file__).resolve().parent
custom_url = os.getenv("MODULE45_DATABASE_URL")

if custom_url:
    connect_args = (
        {"check_same_thread": False}
        if custom_url.startswith("sqlite")
        else {"connect_timeout": 15}
    )
    engine = create_engine(
        custom_url,
        connect_args=connect_args,
        poolclass=NullPool,
    )
else:
    # Reuse the exact psycopg connection from app/db.py that already works on port 5433
    engine = create_engine(
        "postgresql+psycopg://",
        creator=get_db_connection,
        poolclass=NullPool,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()