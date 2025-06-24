"""
Application configuration settings.
"""
import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = Field(default="QA Bot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="qa-bot-index", env="PINECONE_INDEX_NAME")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./qa_bot.db", env="DATABASE_URL")
    
    # Document Processing Configuration
    chunk_size: int = Field(default=1024, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Search Configuration
    similarity_top_k: int = Field(default=5, env="SIMILARITY_TOP_K")
    confidence_threshold: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    
    # File Upload Configuration
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_file_types: List[str] = Field(default=["pdf"], env="ALLOWED_FILE_TYPES")
    max_files_per_upload: int = Field(default=100, env="MAX_FILES_PER_UPLOAD")
    upload_directory: str = Field(default="./uploads", env="UPLOAD_DIRECTORY")
    
    # UI Configuration
    page_title: str = Field(default="QA Bot - Document Question Answering", env="PAGE_TITLE")
    page_icon: str = Field(default="🤖", env="PAGE_ICON")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings