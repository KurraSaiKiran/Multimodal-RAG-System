"""
Vector store implementation using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from src.config import Config
from src.core.embeddings import EmbeddingService
from src.utils.logger import setup_logger, log_execution_time

logger = setup_logger(__name__)


class VectorStore:
    """
    Vector store for storing and retrieving document embeddings using ChromaDB
    """
    
    def __init__(self, collection_name: str = "multimodal_rag"):
        """
        Initialize ChromaDB vector store
        
        Args:
            collection_name: Name of the collection
        """
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService(use_grok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Vector store initialized with collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")
            raise
    
    @log_execution_time
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        if not texts:
            logger.warning("No texts provided to add_documents")
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Validate inputs
        if len(texts) != len(metadatas) or len(texts) != len(ids):
            raise ValueError("texts, metadatas, and ids must have the same length")
        
        try:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents")
            embeddings = self.embedding_service.embed_text(texts)
            
            # Ensure metadatas are properly formatted
            formatted_metadatas = []
            for metadata in metadatas:
                formatted_metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in metadata.items()
                }
                formatted_metadatas.append(formatted_metadata)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=formatted_metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(texts)} documents to vector store")
            return ids
        
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    @log_execution_time
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            Dictionary with query results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query_text)
            
            # Build query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": n_results
            }
            
            if filter_dict:
                query_params["where"] = filter_dict
            
            # Query collection
            results = self.collection.query(**query_params)
            
            # Format results
            formatted_results = {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
            
            logger.info(f"Query returned {len(formatted_results['ids'])} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            raise
    
    @log_execution_time
    def hybrid_query(
        self,
        query_text: str,
        n_results: int = 5,
        keyword_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining dense and sparse retrieval
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            keyword_weight: Weight for keyword search (0-1)
            
        Returns:
            Dictionary with query results
        """
        try:
            # Dense retrieval (semantic search)
            semantic_results = self.query(query_text, n_results=n_results * 2)
            
            # Sparse retrieval (keyword search)
            # ChromaDB doesn't have built-in BM25, so we'll use metadata filtering
            # For a full hybrid search, you'd integrate with Elasticsearch or similar
            
            # For now, we'll just return semantic results with a note
            logger.info("Hybrid search: using semantic results (BM25 not yet implemented)")
            
            return {
                "ids": semantic_results["ids"][:n_results],
                "documents": semantic_results["documents"][:n_results],
                "metadatas": semantic_results["metadatas"][:n_results],
                "distances": semantic_results["distances"][:n_results],
                "search_type": "hybrid_semantic"
            }
        
        except Exception as e:
            logger.error(f"Error in hybrid query: {str(e)}")
            raise
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from the vector store
        
        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_dimension": self.embedding_service.get_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def reset_collection(self) -> None:
        """Reset the collection (delete all documents)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise
