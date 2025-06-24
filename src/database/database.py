"""
Database configuration and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .models import Base

# Database URL from environment variable
# Use in-memory database for Streamlit Cloud (read-only filesystem)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # On Streamlit Cloud, we might not have write permissions
        # This is acceptable for demo purposes
        print(f"Warning: Could not create database tables: {e}")
        pass


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()