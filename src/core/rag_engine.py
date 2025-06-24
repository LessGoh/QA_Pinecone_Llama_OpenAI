"""
RAG (Retrieval-Augmented Generation) engine using LlamaIndex.
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from .config import get_settings
from .vector_store import VectorStore


class RAGEngine:
    """RAG engine for question answering."""

    def __init__(self):
        """Initialize RAG engine components."""
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.vector_store = VectorStore()

    def generate_answer(
        self, 
        query: str, 
        top_k: int = None, 
        confidence_threshold: float = None,
        filter_dict: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate answer for a query using RAG.
        
        Args:
            query: User question
            top_k: Number of relevant chunks to retrieve
            confidence_threshold: Minimum confidence score for results
            filter_dict: Optional metadata filter for search
            
        Returns:
            Answer dictionary with response, sources, and metadata
        """
        start_time = datetime.now()
        
        # Use default values if not provided
        if top_k is None:
            top_k = self.settings.similarity_top_k
        if confidence_threshold is None:
            confidence_threshold = self.settings.confidence_threshold
        
        try:
            # Step 1: Retrieve relevant chunks
            relevant_chunks = self.vector_store.query_vectors(
                query_text=query,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            # Filter by confidence threshold
            filtered_chunks = [
                chunk for chunk in relevant_chunks 
                if chunk["score"] >= confidence_threshold
            ]
            
            if not filtered_chunks:
                return {
                    "answer": "Извините, я не нашел подходящей информации для ответа на ваш вопрос. Попробуйте переформулировать вопрос или загрузить дополнительные документы.",
                    "confidence": 0.0,
                    "sources": [],
                    "response_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                    "retrieved_chunks": 0,
                    "query": query
                }
            
            # Step 2: Prepare context from retrieved chunks
            context_parts = []
            sources = []
            
            for i, chunk in enumerate(filtered_chunks, 1):
                metadata = chunk["metadata"]
                context_parts.append(
                    f"[Источник {i}] (Документ ID: {metadata['document_id']}, "
                    f"Чанк: {metadata['chunk_index']}, Релевантность: {chunk['score']:.3f})\n"
                    f"{metadata['text']}\n"
                )
                
                sources.append({
                    "source_id": i,
                    "document_id": metadata["document_id"],
                    "chunk_index": metadata["chunk_index"],
                    "relevance_score": chunk["score"],
                    "text_preview": metadata["text"][:200] + "..." if len(metadata["text"]) > 200 else metadata["text"]
                })
            
            context = "\n".join(context_parts)
            
            # Step 3: Generate answer using OpenAI
            system_prompt = """Вы - эксперт-помощник по анализу документов. Ваша задача - предоставить точный и полезный ответ на основе предоставленного контекста из документов.

Правила:
1. Отвечайте только на основе предоставленного контекста
2. Если в контексте нет достаточной информации, честно скажите об этом
3. Указывайте источники в формате [Источник N] для подтверждения фактов
4. Отвечайте на том же языке, что и вопрос
5. Будьте конкретными и точными
6. Структурируйте ответ логично и понятно"""

            user_prompt = f"""Контекст из документов:
{context}

Вопрос пользователя: {query}

Предоставьте развернутый ответ на основе контекста, обязательно указывая источники."""

            response = self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content
            
            # Calculate average confidence
            avg_confidence = sum(chunk["score"] for chunk in filtered_chunks) / len(filtered_chunks)
            
            # Calculate response time
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                "answer": answer,
                "confidence": avg_confidence,
                "sources": sources,
                "response_time_ms": response_time_ms,
                "retrieved_chunks": len(filtered_chunks),
                "query": query,
                "success": True
            }
            
        except Exception as e:
            return {
                "answer": f"Произошла ошибка при обработке вашего запроса: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "response_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "retrieved_chunks": 0,
                "query": query,
                "success": False,
                "error": str(e)
            }

    def process_and_index_document(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]) -> bool:
        """
        Process and index document chunks in vector store.
        
        Args:
            document_data: Document metadata
            chunks: List of text chunks
            
        Returns:
            Success status
        """
        try:
            vector_ids = self.vector_store.process_document_chunks(
                chunks=chunks,
                document_id=document_data["id"]
            )
            
            return len(vector_ids) > 0
            
        except Exception as e:
            print(f"Error processing and indexing document: {e}")
            return False

    def delete_document_from_index(self, document_id: int) -> bool:
        """
        Delete all vectors for a document from the index.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Success status
        """
        try:
            return self.vector_store.delete_by_filter({
                "document_id": document_id
            })
        except Exception as e:
            print(f"Error deleting document from index: {e}")
            return False

    def get_document_statistics(self, document_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific document in the index.
        
        Args:
            document_id: Document ID
            
        Returns:
            Statistics dictionary
        """
        try:
            # Query for document chunks
            results = self.vector_store.query_vectors(
                query_text="",  # Empty query to get all chunks
                top_k=1000,
                filter_dict={"document_id": document_id}
            )
            
            if not results:
                return {"chunk_count": 0, "document_id": document_id}
            
            total_chars = sum(
                len(result["metadata"].get("text", "")) 
                for result in results
            )
            
            return {
                "document_id": document_id,
                "chunk_count": len(results),
                "total_characters": total_chars,
                "avg_chunk_size": total_chars // len(results) if results else 0
            }
            
        except Exception as e:
            print(f"Error getting document statistics: {e}")
            return {"error": str(e)}

    def search_similar_content(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar content without generating an answer.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of similar content chunks
        """
        try:
            results = self.vector_store.query_vectors(
                query_text=query,
                top_k=top_k
            )
            
            return [
                {
                    "text": result["metadata"]["text"],
                    "document_id": result["metadata"]["document_id"],
                    "chunk_index": result["metadata"]["chunk_index"],
                    "relevance_score": result["score"]
                }
                for result in results
            ]
            
        except Exception as e:
            print(f"Error searching similar content: {e}")
            return []