import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./apix.db")
ENVIRONMENT = os.environ.get("APP_ENV", "development")

if ENVIRONMENT == "production" and DATABASE_URL.startswith("sqlite"):
    raise ValueError("SQLite is not allowed in production. Set a valid PostgreSQL DATABASE_URL.")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
