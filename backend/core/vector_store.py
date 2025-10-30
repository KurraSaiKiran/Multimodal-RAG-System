import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Any, Optional
from config import Config
from .embeddings import EmbeddingService

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_service = EmbeddingService()
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get or create the main collection"""
        try:
            return self.client.get_collection("multimodal_rag")
        except:
            return self.client.create_collection(
                name="multimodal_rag",
                metadata={"description": "Multimodal RAG collection"}
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store"""
        if not documents:
            return []
        
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            texts.append(doc['content'])
            metadatas.append(doc.get('metadata', {}))
        
        # Generate embeddings
        embeddings = self.embedding_service.encode_batch(texts)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        
        return ids
    
    def search(self, query: str, n_results: int = Config.TOP_K, 
               filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        query_embedding = self.embedding_service.encode_text(query)
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=filter_metadata
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'relevance_score': 1 - results['distances'][0][i]
            })
        
        return formatted_results
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }