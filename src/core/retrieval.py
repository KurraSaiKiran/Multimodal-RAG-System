"""
Retrieval engine with multiple query strategies
"""
from typing import List, Dict, Any, Optional
import numpy as np
from src.core.vector_store import VectorStore
from src.core.embeddings import GrokChatService
from src.utils.logger import setup_logger, log_execution_time
from diskcache import Cache
from src.config import Config

logger = setup_logger(__name__)


class RetrievalEngine:
    """
    Engine for retrieving relevant documents based on queries
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize retrieval engine
        
        Args:
            vector_store: Optional vector store instance
        """
        self.vector_store = vector_store or VectorStore()
        self.grok_service = GrokChatService() if Config.GROK_API_KEY else None
        
        # Initialize cache
        if Config.CACHE_ENABLED:
            self.cache = Cache(Config.CACHE_DIR)
            logger.info("Cache enabled for retrieval")
        else:
            self.cache = None
        
        logger.info("RetrievalEngine initialized")
    
    @log_execution_time
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        strategy: str = "semantic",
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents
        
        Args:
            query: Query string
            n_results: Number of results to return
            strategy: Retrieval strategy ('semantic', 'hybrid', 'expanded')
            filter_dict: Optional metadata filter
            
        Returns:
            Dictionary with retrieval results
        """
        # Check cache first
        cache_key = f"{query}:{n_results}:{strategy}:{str(filter_dict)}"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_result
        
        # Perform retrieval based on strategy
        if strategy == "semantic":
            results = self._semantic_retrieval(query, n_results, filter_dict)
        elif strategy == "hybrid":
            results = self._hybrid_retrieval(query, n_results, filter_dict)
        elif strategy == "expanded":
            results = self._expanded_retrieval(query, n_results, filter_dict)
        else:
            logger.warning(f"Unknown strategy '{strategy}', using semantic")
            results = self._semantic_retrieval(query, n_results, filter_dict)
        
        # Add query to results
        results["query"] = query
        results["strategy"] = strategy
        
        # Cache results
        if self.cache:
            self.cache.set(cache_key, results, expire=3600)  # Cache for 1 hour
        
        return results
    
    def _semantic_retrieval(
        self,
        query: str,
        n_results: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform semantic (dense) retrieval
        
        Args:
            query: Query string
            n_results: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            Retrieval results
        """
        logger.info(f"Performing semantic retrieval for: {query[:50]}...")
        
        results = self.vector_store.query(
            query_text=query,
            n_results=n_results,
            filter_dict=filter_dict
        )
        
        # Convert distances to relevance scores (1 - distance for cosine)
        results["relevance_scores"] = [
            1 - dist for dist in results.get("distances", [])
        ]
        
        return results
    
    def _hybrid_retrieval(
        self,
        query: str,
        n_results: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform hybrid retrieval (dense + sparse)
        
        Args:
            query: Query string
            n_results: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            Retrieval results
        """
        logger.info(f"Performing hybrid retrieval for: {query[:50]}...")
        
        results = self.vector_store.hybrid_query(
            query_text=query,
            n_results=n_results
        )
        
        # Convert distances to relevance scores
        results["relevance_scores"] = [
            1 - dist for dist in results.get("distances", [])
        ]
        
        return results
    
    def _expanded_retrieval(
        self,
        query: str,
        n_results: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform retrieval with query expansion
        
        Args:
            query: Query string
            n_results: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            Retrieval results
        """
        logger.info(f"Performing expanded retrieval for: {query[:50]}...")
        
        # Expand query
        if self.grok_service:
            expanded_queries = self.grok_service.query_expansion(query)
            logger.info(f"Expanded to {len(expanded_queries)} queries")
        else:
            expanded_queries = [query]
        
        # Retrieve for each expanded query
        all_results = []
        seen_ids = set()
        
        for exp_query in expanded_queries:
            results = self.vector_store.query(
                query_text=exp_query,
                n_results=n_results,
                filter_dict=filter_dict
            )
            
            # Add unique results
            for idx, doc_id in enumerate(results.get("ids", [])):
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append({
                        "id": doc_id,
                        "document": results["documents"][idx],
                        "metadata": results["metadatas"][idx],
                        "distance": results["distances"][idx]
                    })
        
        # Sort by distance and take top n
        all_results.sort(key=lambda x: x["distance"])
        top_results = all_results[:n_results]
        
        # Format results
        formatted_results = {
            "ids": [r["id"] for r in top_results],
            "documents": [r["document"] for r in top_results],
            "metadatas": [r["metadata"] for r in top_results],
            "distances": [r["distance"] for r in top_results],
            "relevance_scores": [1 - r["distance"] for r in top_results],
            "expanded_queries": expanded_queries
        }
        
        return formatted_results
    
    @log_execution_time
    def rerank_results(
        self,
        query: str,
        results: Dict[str, Any],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Rerank results using a more sophisticated method
        
        Args:
            query: Original query
            results: Initial retrieval results
            top_k: Number of top results to return after reranking
            
        Returns:
            Reranked results
        """
        logger.info(f"Reranking {len(results.get('ids', []))} results")
        
        # Simple reranking based on multiple factors
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        distances = results.get("distances", [])
        
        if not documents:
            return results
        
        # Calculate reranking scores
        rerank_scores = []
        for idx, (doc, metadata, dist) in enumerate(zip(documents, metadatas, distances)):
            score = 0.0
            
            # Base semantic score (1 - distance)
            semantic_score = 1 - dist
            score += semantic_score * 0.7
            
            # Length penalty (prefer moderate length documents)
            doc_length = len(doc)
            optimal_length = 500
            length_score = 1 - abs(doc_length - optimal_length) / (optimal_length * 2)
            length_score = max(0, length_score)
            score += length_score * 0.1
            
            # Recency bonus (if timestamp available)
            if "upload_timestamp" in metadata:
                # Could add recency scoring here
                pass
            
            # File type preference (prefer mixed content)
            file_type = metadata.get("file_type", "unknown")
            if file_type == "pdf":
                score += 0.1
            
            rerank_scores.append(score)
        
        # Sort by rerank score
        sorted_indices = np.argsort(rerank_scores)[::-1][:top_k]
        
        # Reorder results
        reranked_results = {
            "ids": [results["ids"][i] for i in sorted_indices],
            "documents": [results["documents"][i] for i in sorted_indices],
            "metadatas": [results["metadatas"][i] for i in sorted_indices],
            "distances": [results["distances"][i] for i in sorted_indices],
            "relevance_scores": [rerank_scores[i] for i in sorted_indices],
            "reranked": True
        }
        
        logger.info(f"Reranked to top {len(sorted_indices)} results")
        return reranked_results
    
    @log_execution_time
    def answer_query(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve documents and generate an answer
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            
        Returns:
            Dictionary with answer and source documents
        """
        # Retrieve relevant documents
        results = self.retrieve(query, n_results=n_results, strategy="expanded")
        
        # Generate answer using Grok
        answer = None
        if self.grok_service:
            context = results.get("documents", [])
            answer = self.grok_service.answer_with_context(query, context)
        
        return {
            "query": query,
            "answer": answer,
            "sources": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "relevance_scores": results.get("relevance_scores", [])
        }
    
    def clear_cache(self):
        """Clear the retrieval cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Retrieval cache cleared")
