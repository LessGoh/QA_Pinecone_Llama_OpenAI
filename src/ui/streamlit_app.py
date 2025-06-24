"""
Streamlit web application for the QA Bot.
"""
import streamlit as st
import os
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import get_settings
from src.core.pdf_processor import PDFProcessor
from src.core.rag_engine import RAGEngine
from src.database.database import get_db, create_tables
from src.database.crud import DocumentCRUD, ChunkCRUD, QueryHistoryCRUD, UserCRUD


class QABotApp:
    """Main QA Bot Streamlit application."""

    def __init__(self):
        """Initialize the application."""
        self.settings = get_settings()
        self.pdf_processor = PDFProcessor()
        self.rag_engine = RAGEngine()
        
        # Initialize database
        create_tables()
        
        # Initialize session state
        self._init_session_state()

    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 1  # Default user
        
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        if 'processed_documents' not in st.session_state:
            st.session_state.processed_documents = []

    def run(self):
        """Run the Streamlit application."""
        st.set_page_config(
            page_title=self.settings.page_title,
            page_icon=self.settings.page_icon,
            layout="wide"
        )
        
        st.title("🤖 QA Bot - Document Question Answering")
        st.markdown("---")
        
        # Sidebar for configuration and document management
        self._render_sidebar()
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_query_interface()
        
        with col2:
            self._render_document_status()

    def _render_sidebar(self):
        """Render the sidebar with document upload and management."""
        st.sidebar.header("📄 Document Management")
        
        # Document upload section
        st.sidebar.subheader("Upload Documents")
        uploaded_files = st.sidebar.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help=f"Upload up to {self.settings.max_files_per_upload} PDF files (max {self.settings.max_file_size_mb}MB each)"
        )
        
        if uploaded_files:
            if st.sidebar.button("Process Documents", type="primary"):
                self._process_uploaded_files(uploaded_files)
        
        # Document list section
        st.sidebar.subheader("📚 Document Library")
        self._render_document_library()
        
        # Settings section
        st.sidebar.subheader("⚙️ Query Settings")
        
        similarity_top_k = st.sidebar.slider(
            "Number of results to retrieve",
            min_value=1,
            max_value=20,
            value=self.settings.similarity_top_k,
            help="How many relevant document chunks to use for answering"
        )
        
        confidence_threshold = st.sidebar.slider(
            "Confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=self.settings.confidence_threshold,
            step=0.1,
            help="Minimum relevance score for document chunks"
        )
        
        # Store settings in session state
        st.session_state.similarity_top_k = similarity_top_k
        st.session_state.confidence_threshold = confidence_threshold

    def _render_query_interface(self):
        """Render the main query interface."""
        st.header("❓ Ask Questions")
        
        # Query input
        query = st.text_area(
            "Enter your question:",
            height=100,
            placeholder="Например: Что такое машинное обучение? Какие методы анализа данных описаны в документах?"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            ask_button = st.button("🔍 Ask Question", type="primary")
        
        with col2:
            clear_history = st.button("🗑️ Clear History")
        
        if clear_history:
            st.session_state.query_history = []
            st.rerun()
        
        # Process query
        if ask_button and query.strip():
            with st.spinner("Searching for answers..."):
                result = self._process_query(query.strip())
                self._display_answer(result)
        
        # Display query history
        if st.session_state.query_history:
            st.subheader("📝 Recent Questions & Answers")
            for i, item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                with st.expander(f"Q{i}: {item['query'][:100]}{'...' if len(item['query']) > 100 else ''}"):
                    self._display_answer(item['result'])

    def _render_document_status(self):
        """Render document processing status and statistics."""
        st.header("📊 System Status")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Document statistics
            documents = DocumentCRUD.get_all_documents(db)
            
            st.metric("📄 Total Documents", len(documents))
            
            if documents:
                total_pages = sum(doc.total_pages or 0 for doc in documents)
                st.metric("📖 Total Pages", total_pages)
            
            # Vector store statistics
            try:
                stats = self.rag_engine.vector_store.get_index_stats()
                if stats:
                    st.metric("🔢 Vector Count", stats.get("total_vector_count", 0))
                    st.metric("📈 Index Fullness", f"{stats.get('index_fullness', 0):.2%}")
            except:
                st.info("Vector store statistics unavailable")
            
            # Recent queries
            if st.session_state.query_history:
                avg_response_time = sum(
                    item['result']['response_time_ms'] 
                    for item in st.session_state.query_history
                ) / len(st.session_state.query_history)
                st.metric("⚡ Avg Response Time", f"{avg_response_time:.0f}ms")
        
        finally:
            db.close()

    def _render_document_library(self):
        """Render the document library in sidebar."""
        db = next(get_db())
        
        try:
            documents = DocumentCRUD.get_all_documents(db, limit=20)
            
            if not documents:
                st.sidebar.info("No documents uploaded yet")
                return
            
            for doc in documents:
                with st.sidebar.expander(f"📄 {doc.name}"):
                    st.write(f"**Size:** {doc.file_size / (1024*1024):.2f} MB")
                    st.write(f"**Pages:** {doc.total_pages or 'Unknown'}")
                    st.write(f"**Uploaded:** {doc.upload_date.strftime('%Y-%m-%d %H:%M')}")
                    
                    if st.button(f"🗑️ Delete", key=f"delete_{doc.id}"):
                        self._delete_document(doc.id)
                        st.rerun()
        
        finally:
            db.close()

    def _process_uploaded_files(self, uploaded_files: List[Any]):
        """Process uploaded PDF files."""
        if len(uploaded_files) > self.settings.max_files_per_upload:
            st.error(f"Too many files! Maximum allowed: {self.settings.max_files_per_upload}")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        db = next(get_db())
        
        try:
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = Path(tmp_file.name)
                
                try:
                    # Validate PDF
                    validation = self.pdf_processor.validate_pdf_file(tmp_path)
                    if not validation["valid"]:
                        st.error(f"❌ {uploaded_file.name}: {validation['error']}")
                        continue
                    
                    # Check for duplicate
                    file_hash = self.pdf_processor.calculate_file_hash(tmp_path)
                    existing_doc = DocumentCRUD.get_document_by_hash(db, file_hash)
                    if existing_doc:
                        st.warning(f"⚠️ {uploaded_file.name}: Document already exists")
                        continue
                    
                    # Extract text
                    extraction_result = self.pdf_processor.extract_text_from_pdf(tmp_path)
                    if not extraction_result["success"]:
                        st.error(f"❌ {uploaded_file.name}: Text extraction failed")
                        continue
                    
                    # Create document record
                    document = DocumentCRUD.create_document(
                        db,
                        name=uploaded_file.name,
                        original_filename=uploaded_file.name,
                        file_path=str(tmp_path),
                        file_size=uploaded_file.size,
                        content_hash=file_hash,
                        total_pages=extraction_result["total_pages"],
                        author=extraction_result["metadata"].get("author"),
                        processed_at=datetime.utcnow()
                    )
                    
                    # Create chunks
                    chunks = self.pdf_processor.chunk_text(
                        extraction_result["full_text"],
                        chunk_size=self.settings.chunk_size,
                        overlap=self.settings.chunk_overlap
                    )
                    
                    # Process chunks and create vector embeddings
                    success = self.rag_engine.process_and_index_document(
                        document_data={"id": document.id},
                        chunks=chunks
                    )
                    
                    if success:
                        # Store chunk information in database
                        for chunk in chunks:
                            ChunkCRUD.create_chunk(
                                db,
                                document_id=document.id,
                                content=chunk["text"],
                                chunk_index=chunk["chunk_index"],
                                token_count=chunk["estimated_tokens"],
                                vector_id=f"doc_{document.id}_chunk_{chunk['chunk_index']}"
                            )
                        
                        st.success(f"✅ {uploaded_file.name}: Processed successfully ({len(chunks)} chunks)")
                    else:
                        st.error(f"❌ {uploaded_file.name}: Vector indexing failed")
                        # Clean up document record if vector indexing failed
                        DocumentCRUD.delete_document(db, document.id)
                
                finally:
                    # Clean up temporary file
                    if tmp_path.exists():
                        tmp_path.unlink()
        
        finally:
            db.close()
            progress_bar.empty()
            status_text.empty()

    def _process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return the result."""
        # Get settings from session state
        similarity_top_k = st.session_state.get('similarity_top_k', self.settings.similarity_top_k)
        confidence_threshold = st.session_state.get('confidence_threshold', self.settings.confidence_threshold)
        
        # Generate answer
        result = self.rag_engine.generate_answer(
            query=query,
            top_k=similarity_top_k,
            confidence_threshold=confidence_threshold
        )
        
        # Store in query history
        query_item = {
            "query": query,
            "result": result,
            "timestamp": datetime.now()
        }
        st.session_state.query_history.append(query_item)
        
        # Store in database
        db = next(get_db())
        try:
            QueryHistoryCRUD.create_query_history(
                db,
                user_id=st.session_state.user_id,
                query=query,
                response=result["answer"],
                confidence_score=result["confidence"],
                response_time_ms=result["response_time_ms"],
                sources_used=str(result["sources"]),
                session_id=st.session_state.session_id
            )
        finally:
            db.close()
        
        return result

    def _display_answer(self, result: Dict[str, Any]):
        """Display the answer and related information."""
        if not result.get("success", True):
            st.error(f"Error: {result.get('error', 'Unknown error')}")
            return
        
        # Main answer
        st.markdown("### 💡 Answer")
        st.markdown(result["answer"])
        
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⚡ Response Time", f"{result['response_time_ms']}ms")
        with col2:
            st.metric("🎯 Confidence", f"{result['confidence']:.2%}")
        with col3:
            st.metric("📝 Sources Used", result['retrieved_chunks'])
        
        # Sources
        if result["sources"]:
            st.markdown("### 📚 Sources")
            for source in result["sources"]:
                with st.expander(f"Source {source['source_id']} (Relevance: {source['relevance_score']:.3f})"):
                    st.write(f"**Document ID:** {source['document_id']}")
                    st.write(f"**Chunk:** {source['chunk_index']}")
                    st.write("**Content Preview:**")
                    st.text(source['text_preview'])

    def _delete_document(self, document_id: int):
        """Delete a document and its associated data."""
        db = next(get_db())
        
        try:
            # Delete from vector store
            success = self.rag_engine.delete_document_from_index(document_id)
            if success:
                # Delete from database
                DocumentCRUD.delete_document(db, document_id)
                st.success("Document deleted successfully!")
            else:
                st.error("Failed to delete document from vector store")
        
        finally:
            db.close()


def main():
    """Main function to run the Streamlit app."""
    try:
        app = QABotApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()