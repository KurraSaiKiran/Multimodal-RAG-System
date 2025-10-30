"""
Embedding service using Grok API and local models
"""
import openai
import numpy as np
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
from src.config import Config
from src.utils.logger import setup_logger, log_execution_time

logger = setup_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using Grok API or local models
    """
    
    def __init__(self, use_grok: bool = True):
        """
        Initialize embedding service
        
        Args:
            use_grok: Whether to use Grok API (True) or local models (False)
        """
        self.use_grok = use_grok and bool(Config.GROK_API_KEY)
        
        if self.use_grok:
            logger.info("Initializing Grok API for embeddings")
            self.client = openai.OpenAI(
                api_key=Config.GROK_API_KEY,
                base_url=Config.GROK_API_BASE
            )
            self.model_name = "grok-1"
        else:
            logger.info(f"Initializing local embedding model: {Config.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
            self.model_name = Config.EMBEDDING_MODEL
        
        logger.info(f"EmbeddingService initialized with {'Grok API' if self.use_grok else 'local model'}")
    
    @log_execution_time
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Embedding vector(s)
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        if not texts:
            return [] if not is_single else []
        
        try:
            if self.use_grok:
                embeddings = self._embed_with_grok(texts)
            else:
                embeddings = self._embed_with_local(texts)
            
            return embeddings[0] if is_single else embeddings
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _embed_with_grok(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Grok API
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            # Note: This is a placeholder. Grok API may not have a direct embedding endpoint
            # We'll use chat completion to generate semantic representations
            # In production, you'd want to use a dedicated embedding API
            
            logger.warning("Grok API embedding endpoint not yet available, falling back to local model")
            return self._embed_with_local(texts)
            
        except Exception as e:
            logger.error(f"Grok API embedding failed: {str(e)}")
            logger.info("Falling back to local embedding model")
            return self._embed_with_local(texts)
    
    def _embed_with_local(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using local model
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if not hasattr(self, 'model'):
            logger.info(f"Loading local model: {Config.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service
        
        Returns:
            Embedding dimension
        """
        if self.use_grok:
            # Grok embeddings dimension (placeholder)
            return 768
        else:
            return self.model.get_sentence_embedding_dimension()
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


class GrokChatService:
    """
    Service for using Grok for chat completions and query understanding
    """
    
    def __init__(self):
        """Initialize Grok chat service"""
        if not Config.GROK_API_KEY:
            raise ValueError("GROK_API_KEY is required for GrokChatService")
        
        self.client = openai.OpenAI(
            api_key=Config.GROK_API_KEY,
            base_url=Config.GROK_API_BASE
        )
        logger.info("GrokChatService initialized")
    
    @log_execution_time
    def query_expansion(self, query: str) -> List[str]:
        """
        Expand a query into multiple related queries
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        try:
            prompt = f"""Given this query: "{query}"
            
Generate 3 different variations of this query that could help find relevant information. 
Return only the queries, one per line, without numbering or explanation."""

            response = self.client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            expanded = response.choices[0].message.content.strip().split('\n')
            expanded = [q.strip() for q in expanded if q.strip()]
            
            logger.info(f"Expanded query into {len(expanded)} variations")
            return [query] + expanded
        
        except Exception as e:
            logger.error(f"Query expansion failed: {str(e)}")
            return [query]
    
    @log_execution_time
    def answer_with_context(self, query: str, context: List[str]) -> str:
        """
        Generate answer using retrieved context
        
        Args:
            query: User query
            context: Retrieved context chunks
            
        Returns:
            Generated answer
        """
        try:
            context_text = "\n\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(context)])
            
            prompt = f"""Answer the following query using the provided context. If the context doesn't contain enough information, say so.

Query: {query}

Context:
{context_text}

Answer:"""

            response = self.client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info("Generated answer using Grok")
            return answer
        
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            return f"Error generating answer: {str(e)}"
