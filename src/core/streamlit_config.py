"""
Streamlit-specific configuration handler.
"""
import streamlit as st
from typing import Optional, List
from pydantic import BaseModel


class StreamlitSettings(BaseModel):
    """Streamlit-specific settings using st.secrets."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    
    # Pinecone Configuration
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str = "qa-bot-index"
    
    # Database Configuration
    database_url: str = "sqlite:///./qa_bot.db"
    
    # Application Configuration
    app_name: str = "QA Bot"
    app_version: str = "1.0.0"
    debug: bool = False
    page_title: str = "QA Bot - Document Question Answering"
    page_icon: str = "🤖"
    
    # Processing Configuration
    chunk_size: int = 1024
    chunk_overlap: int = 200
    similarity_top_k: int = 5
    confidence_threshold: float = 0.7
    
    # Upload Configuration
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = ["pdf"]
    max_files_per_upload: int = 100
    upload_directory: str = "./uploads"


def get_streamlit_settings() -> StreamlitSettings:
    """
    Get settings from Streamlit secrets.
    
    Returns:
        StreamlitSettings instance with all configuration
    """
    try:
        return StreamlitSettings(
            # OpenAI
            openai_api_key=st.secrets["openai"]["api_key"],
            openai_model=st.secrets["openai"].get("model", "gpt-4"),
            embedding_model=st.secrets["openai"].get("embedding_model", "text-embedding-ada-002"),
            
            # Pinecone
            pinecone_api_key=st.secrets["pinecone"]["api_key"],
            pinecone_environment=st.secrets["pinecone"]["environment"],
            pinecone_index_name=st.secrets["pinecone"].get("index_name", "qa-bot-index"),
            
            # Database
            database_url=st.secrets["database"].get("url", "sqlite:///./qa_bot.db"),
            
            # App
            app_name=st.secrets["app"].get("name", "QA Bot"),
            app_version=st.secrets["app"].get("version", "1.0.0"),
            debug=st.secrets["app"].get("debug", False),
            page_title=st.secrets["app"].get("page_title", "QA Bot - Document Question Answering"),
            page_icon=st.secrets["app"].get("page_icon", "🤖"),
            
            # Processing
            chunk_size=st.secrets["processing"].get("chunk_size", 1024),
            chunk_overlap=st.secrets["processing"].get("chunk_overlap", 200),
            similarity_top_k=st.secrets["processing"].get("similarity_top_k", 5),
            confidence_threshold=st.secrets["processing"].get("confidence_threshold", 0.7),
            
            # Upload
            max_file_size_mb=st.secrets["upload"].get("max_file_size_mb", 50),
            allowed_file_types=st.secrets["upload"].get("allowed_file_types", ["pdf"]),
            max_files_per_upload=st.secrets["upload"].get("max_files_per_upload", 100),
            upload_directory=st.secrets["upload"].get("upload_directory", "./uploads")
        )
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации: {str(e)}")
        st.info("Убедитесь, что файл .streamlit/secrets.toml настроен правильно")
        st.stop()