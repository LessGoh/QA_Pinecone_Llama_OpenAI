"""
Vector store operations using Pinecone.
"""
import os
from typing import List, Dict, Any, Optional
import pinecone
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from .config import get_settings


class VectorStore:
    """Pinecone vector store manager."""

    def __init__(self):
        """Initialize Pinecone and OpenAI clients."""
        self.settings = get_settings()
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index_name = self.settings.pinecone_index_name
        
        # Initialize OpenAI for embeddings
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        
        # Initialize index
        self.index = None
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists."""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.settings.pinecone_environment
                    )
                )
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            print(f"Error setting up Pinecone index: {e}")
            raise

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts using OpenAI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.settings.embedding_model,
                input=texts
            )
            
            embeddings = [embedding.embedding for embedding in response.data]
            return embeddings
            
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            raise

    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        Upsert vectors to Pinecone index.
        
        Args:
            vectors: List of vector dictionaries with id, values, and metadata
            
        Returns:
            Success status
        """
        try:
            # Batch upsert vectors
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            print(f"Successfully upserted {len(vectors)} vectors")
            return True
            
        except Exception as e:
            print(f"Error upserting vectors: {e}")
            return False

    def query_vectors(self, query_text: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Query vectors from Pinecone index.
        
        Args:
            query_text: Query text to search for
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of query results with metadata
        """
        try:
            # Create embedding for query
            query_embedding = self.create_embeddings([query_text])[0]
            
            # Query index
            query_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in query_response.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            return results
            
        except Exception as e:
            print(f"Error querying vectors: {e}")
            return []

    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """
        Delete vectors from Pinecone index.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            Success status
        """
        try:
            self.index.delete(ids=vector_ids)
            print(f"Successfully deleted {len(vector_ids)} vectors")
            return True
            
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False

    def delete_by_filter(self, filter_dict: Dict) -> bool:
        """
        Delete vectors by metadata filter.
        
        Args:
            filter_dict: Metadata filter for deletion
            
        Returns:
            Success status
        """
        try:
            self.index.delete(filter=filter_dict)
            print(f"Successfully deleted vectors with filter: {filter_dict}")
            return True
            
        except Exception as e:
            print(f"Error deleting vectors by filter: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Index statistics dictionary
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {}

    def process_document_chunks(self, chunks: List[Dict[str, Any]], document_id: int) -> List[str]:
        """
        Process document chunks and store in vector database.
        
        Args:
            chunks: List of text chunks with metadata
            document_id: Document ID for reference
            
        Returns:
            List of vector IDs created
        """
        try:
            # Create embeddings for all chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.create_embeddings(chunk_texts)
            
            # Prepare vectors for upsert
            vectors = []
            vector_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"
                vector_ids.append(vector_id)
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": chunk["chunk_index"],
                        "text": chunk["text"],
                        "char_count": chunk["char_count"],
                        "estimated_tokens": chunk["estimated_tokens"],
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"]
                    }
                })
            
            # Upsert to Pinecone
            success = self.upsert_vectors(vectors)
            
            if success:
                return vector_ids
            else:
                return []
                
        except Exception as e:
            print(f"Error processing document chunks: {e}")
            return []