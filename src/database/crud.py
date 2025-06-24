"""
CRUD operations for database models.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models


class UserCRUD:
    """CRUD operations for User model."""

    @staticmethod
    def create_user(db: Session, name: str, email: str, role: str = "user") -> models.User:
        """Create a new user."""
        db_user = models.User(name=name, email=email, role=role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
        """Get user by ID."""
        return db.query(models.User).filter(models.User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email."""
        return db.query(models.User).filter(models.User.email == email).first()

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[models.User]:
        """Update user."""
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user."""
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False


class DocumentCRUD:
    """CRUD operations for Document model."""

    @staticmethod
    def create_document(db: Session, **kwargs) -> models.Document:
        """Create a new document."""
        db_document = models.Document(**kwargs)
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document

    @staticmethod
    def get_document_by_id(db: Session, document_id: int) -> Optional[models.Document]:
        """Get document by ID."""
        return db.query(models.Document).filter(models.Document.id == document_id).first()

    @staticmethod
    def get_document_by_hash(db: Session, content_hash: str) -> Optional[models.Document]:
        """Get document by content hash."""
        return db.query(models.Document).filter(models.Document.content_hash == content_hash).first()

    @staticmethod
    def get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Document]:
        """Get all documents with pagination."""
        return db.query(models.Document).offset(skip).limit(limit).all()

    @staticmethod
    def update_document(db: Session, document_id: int, **kwargs) -> Optional[models.Document]:
        """Update document."""
        db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if db_document:
            for key, value in kwargs.items():
                setattr(db_document, key, value)
            db.commit()
            db.refresh(db_document)
        return db_document

    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        """Delete document and its chunks."""
        db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if db_document:
            db.delete(db_document)
            db.commit()
            return True
        return False


class ChunkCRUD:
    """CRUD operations for Chunk model."""

    @staticmethod
    def create_chunk(db: Session, **kwargs) -> models.Chunk:
        """Create a new chunk."""
        db_chunk = models.Chunk(**kwargs)
        db.add(db_chunk)
        db.commit()
        db.refresh(db_chunk)
        return db_chunk

    @staticmethod
    def get_chunks_by_document(db: Session, document_id: int) -> List[models.Chunk]:
        """Get all chunks for a document."""
        return db.query(models.Chunk).filter(models.Chunk.document_id == document_id).all()

    @staticmethod
    def get_chunk_by_vector_id(db: Session, vector_id: str) -> Optional[models.Chunk]:
        """Get chunk by vector ID."""
        return db.query(models.Chunk).filter(models.Chunk.vector_id == vector_id).first()

    @staticmethod
    def delete_chunks_by_document(db: Session, document_id: int) -> bool:
        """Delete all chunks for a document."""
        result = db.query(models.Chunk).filter(models.Chunk.document_id == document_id).delete()
        db.commit()
        return result > 0


class QueryHistoryCRUD:
    """CRUD operations for QueryHistory model."""

    @staticmethod
    def create_query_history(db: Session, **kwargs) -> models.QueryHistory:
        """Create a new query history entry."""
        db_query = models.QueryHistory(**kwargs)
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        return db_query

    @staticmethod
    def get_user_query_history(db: Session, user_id: int, limit: int = 50) -> List[models.QueryHistory]:
        """Get query history for a user."""
        return (
            db.query(models.QueryHistory)
            .filter(models.QueryHistory.user_id == user_id)
            .order_by(models.QueryHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_session_query_history(db: Session, session_id: str) -> List[models.QueryHistory]:
        """Get query history for a session."""
        return (
            db.query(models.QueryHistory)
            .filter(models.QueryHistory.session_id == session_id)
            .order_by(models.QueryHistory.timestamp.asc())
            .all()
        )