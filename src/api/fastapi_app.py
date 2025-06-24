"""
FastAPI application for QA Bot REST API.
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import get_settings
from src.core.pdf_processor import PDFProcessor
from src.core.rag_engine import RAGEngine
from src.database.database import get_db, create_tables
from src.database.crud import DocumentCRUD, QueryHistoryCRUD


class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    similarity_top_k: Optional[int] = None
    confidence_threshold: Optional[float] = None
    document_ids: Optional[List[int]] = None


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    response_time_ms: int
    retrieved_chunks: int
    query: str
    success: bool
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information model."""
    id: int
    name: str
    file_size: int
    total_pages: Optional[int]
    upload_date: datetime
    processed: bool


# Initialize FastAPI app
app = FastAPI(
    title="QA Bot API",
    description="REST API for document-based question answering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
settings = get_settings()
pdf_processor = PDFProcessor()
rag_engine = RAGEngine()

# Create database tables
create_tables()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "QA Bot API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check vector store connection
        stats = rag_engine.vector_store.get_index_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_store": "connected" if stats else "disconnected",
            "vector_count": stats.get("total_vector_count", 0) if stats else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.post("/upload", response_model=List[DocumentInfo])
async def upload_documents(
    files: List[UploadFile] = File(...),
    db=Depends(get_db)
):
    """
    Upload and process PDF documents.
    
    Args:
        files: List of PDF files to upload
        db: Database session
        
    Returns:
        List of processed document information
    """
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum allowed: {settings.max_files_per_upload}"
        )
    
    processed_docs = []
    errors = []
    
    for uploaded_file in files:
        try:
            # Validate file type
            if not uploaded_file.filename.lower().endswith('.pdf'):
                errors.append(f"{uploaded_file.filename}: Not a PDF file")
                continue
            
            # Validate file size
            if uploaded_file.size > settings.max_file_size_mb * 1024 * 1024:
                errors.append(f"{uploaded_file.filename}: File too large")
                continue
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                content = await uploaded_file.read()
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)
            
            try:
                # Validate PDF
                validation = pdf_processor.validate_pdf_file(tmp_path)
                if not validation["valid"]:
                    errors.append(f"{uploaded_file.filename}: {validation['error']}")
                    continue
                
                # Check for duplicate
                file_hash = pdf_processor.calculate_file_hash(tmp_path)
                existing_doc = DocumentCRUD.get_document_by_hash(db, file_hash)
                if existing_doc:
                    processed_docs.append(DocumentInfo(
                        id=existing_doc.id,
                        name=existing_doc.name,
                        file_size=existing_doc.file_size,
                        total_pages=existing_doc.total_pages,
                        upload_date=existing_doc.upload_date,
                        processed=True
                    ))
                    continue
                
                # Extract text
                extraction_result = pdf_processor.extract_text_from_pdf(tmp_path)
                if not extraction_result["success"]:
                    errors.append(f"{uploaded_file.filename}: Text extraction failed")
                    continue
                
                # Create document record
                document = DocumentCRUD.create_document(
                    db,
                    name=uploaded_file.filename,
                    original_filename=uploaded_file.filename,
                    file_path=str(tmp_path),
                    file_size=uploaded_file.size,
                    content_hash=file_hash,
                    total_pages=extraction_result["total_pages"],
                    author=extraction_result["metadata"].get("author"),
                    processed_at=datetime.utcnow()
                )
                
                # Create chunks
                chunks = pdf_processor.chunk_text(
                    extraction_result["full_text"],
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap
                )
                
                # Process chunks and create vector embeddings
                success = rag_engine.process_and_index_document(
                    document_data={"id": document.id},
                    chunks=chunks
                )
                
                if success:
                    processed_docs.append(DocumentInfo(
                        id=document.id,
                        name=document.name,
                        file_size=document.file_size,
                        total_pages=document.total_pages,
                        upload_date=document.upload_date,
                        processed=True
                    ))
                else:
                    errors.append(f"{uploaded_file.filename}: Vector indexing failed")
                    DocumentCRUD.delete_document(db, document.id)
            
            finally:
                # Clean up temporary file
                if tmp_path.exists():
                    tmp_path.unlink()
        
        except Exception as e:
            errors.append(f"{uploaded_file.filename}: {str(e)}")
    
    if errors:
        return JSONResponse(
            status_code=207,  # Multi-status
            content={
                "processed_documents": [doc.dict() for doc in processed_docs],
                "errors": errors
            }
        )
    
    return processed_docs


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db=Depends(get_db)
):
    """
    Query documents for answers.
    
    Args:
        request: Query request with question and parameters
        db: Database session
        
    Returns:
        Query response with answer and sources
    """
    try:
        # Prepare filter if document IDs specified
        filter_dict = None
        if request.document_ids:
            filter_dict = {
                "document_id": {"$in": request.document_ids}
            }
        
        # Generate answer
        result = rag_engine.generate_answer(
            query=request.query,
            top_k=request.similarity_top_k,
            confidence_threshold=request.confidence_threshold,
            filter_dict=filter_dict
        )
        
        # Store query in database
        try:
            QueryHistoryCRUD.create_query_history(
                db,
                user_id=1,  # Default API user
                query=request.query,
                response=result["answer"],
                confidence_score=result["confidence"],
                response_time_ms=result["response_time_ms"],
                sources_used=str(result["sources"]),
                session_id=str(uuid.uuid4())
            )
        except Exception as e:
            print(f"Error storing query history: {e}")
        
        return QueryResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """
    List uploaded documents.
    
    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        db: Database session
        
    Returns:
        List of document information
    """
    try:
        documents = DocumentCRUD.get_all_documents(db, skip=skip, limit=limit)
        return [
            DocumentInfo(
                id=doc.id,
                name=doc.name,
                file_size=doc.file_size,
                total_pages=doc.total_pages,
                upload_date=doc.upload_date,
                processed=doc.processed_at is not None
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db=Depends(get_db)
):
    """
    Delete a document and its associated data.
    
    Args:
        document_id: ID of document to delete
        db: Database session
        
    Returns:
        Deletion status
    """
    try:
        # Check if document exists
        document = DocumentCRUD.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        success = rag_engine.delete_document_from_index(document_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete from vector store")
        
        # Delete from database
        DocumentCRUD.delete_document(db, document_id)
        
        return {"message": "Document deleted successfully", "document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/stats")
async def get_document_stats(document_id: int, db=Depends(get_db)):
    """
    Get statistics for a specific document.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Document statistics
    """
    try:
        # Check if document exists
        document = DocumentCRUD.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get vector store statistics
        stats = rag_engine.get_document_statistics(document_id)
        
        return {
            "document_id": document_id,
            "name": document.name,
            "file_size": document.file_size,
            "total_pages": document.total_pages,
            "upload_date": document.upload_date,
            "vector_stats": stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_content(
    query: str,
    top_k: int = 10,
    db=Depends(get_db)
):
    """
    Search for similar content without generating an answer.
    
    Args:
        query: Search query
        top_k: Number of results to return
        db: Database session
        
    Returns:
        List of similar content chunks
    """
    try:
        results = rag_engine.search_similar_content(query, top_k)
        return {"query": query, "results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)