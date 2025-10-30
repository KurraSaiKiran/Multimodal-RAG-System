import re
from typing import List, Dict, Any, Optional
from groq import Groq
from config import Config
from .vector_store import VectorStore

class QueryEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        
    def classify_query_type(self, query: str) -> str:
        """Classify query type for appropriate retrieval strategy"""
        query_lower = query.lower()
        
        # Specific factual questions
        factual_patterns = [
            r'\bwhat is\b', r'\bwho is\b', r'\bwhen did\b', r'\bwhere is\b',
            r'\bhow many\b', r'\bdefine\b', r'\bexplain\b'
        ]
        
        # Cross-modal queries
        cross_modal_patterns = [
            r'\bimage\b', r'\bpicture\b', r'\bphoto\b', r'\bvisual\b',
            r'\bshow\b.*\bimage\b', r'\bdescribe.*image\b'
        ]
        
        # Vague/exploratory queries
        vague_patterns = [
            r'\btell me about\b', r'\binformation about\b', r'\banything about\b',
            r'\brelated to\b', r'\bsimilar to\b'
        ]
        
        for pattern in factual_patterns:
            if re.search(pattern, query_lower):
                return 'factual'
        
        for pattern in cross_modal_patterns:
            if re.search(pattern, query_lower):
                return 'cross_modal'
        
        for pattern in vague_patterns:
            if re.search(pattern, query_lower):
                return 'exploratory'
        
        return 'general'
    
    def retrieve_documents(self, query: str, query_type: str = None, 
                          content_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on query and type"""
        if not query_type:
            query_type = self.classify_query_type(query)
        
        # Adjust retrieval parameters based on query type
        n_results = Config.TOP_K
        filter_metadata = {}
        
        if query_type == 'factual':
            n_results = 3  # Fewer, more precise results
        elif query_type == 'exploratory':
            n_results = 8  # More results for exploration
        elif query_type == 'cross_modal':
            # Don't filter by content type for cross-modal queries
            pass
        
        if content_type_filter:
            filter_metadata['content_type'] = content_type_filter
        
        results = self.vector_store.search(
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Return all results if we have any, otherwise lower threshold
        if results:
            return results
        
        # If no results, try with lower threshold
        return self.vector_store.search(
            query=query,
            n_results=n_results,
            filter_metadata=None  # Remove filters for broader search
        )
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using Groq API with retrieved context"""
        if not context_docs:
            return {
                'response': "I couldn't find any relevant information in your uploaded documents to answer this question. Please try uploading some documents first, or ask a different question about the content you've already uploaded.",
                'sources': [],
                'query_type': self.classify_query_type(query),
                'context_used': 0
            }
        
        # Prepare context
        context_text = ""
        sources = []
        
        for i, doc in enumerate(context_docs):
            context_text += f"Document {i+1}:\n{doc['content']}\n\n"
            sources.append({
                'source': doc['metadata'].get('source', 'Unknown'),
                'content_type': doc['metadata'].get('content_type', 'Unknown'),
                'relevance_score': doc['relevance_score']
            })
        
        # Create prompt for better responses
        prompt = f"""You are a helpful assistant. Answer the user's question based on the provided context documents. 
Provide a clear, concise, and easy-to-understand answer. If the context doesn't contain enough information, say so politely.

Context Documents:
{context_text}

User Question: {query}

Please provide a helpful answer:"""
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and easy-to-understand answers based on the given context. Use simple language and explain concepts when needed."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                max_tokens=1500,
                temperature=0.3
            )
            
            return {
                'response': response.choices[0].message.content,
                'sources': sources,
                'query_type': self.classify_query_type(query),
                'context_used': len(context_docs)
            }
            
        except Exception as e:
            return {
                'response': f"Error generating response: {str(e)}",
                'sources': sources,
                'query_type': self.classify_query_type(query)
            }
    
    def query(self, query_text: str, content_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """Main query method"""
        query_type = self.classify_query_type(query_text)
        
        # Retrieve relevant documents
        relevant_docs = self.retrieve_documents(
            query=query_text,
            query_type=query_type,
            content_type_filter=content_type_filter
        )
        
        # Generate response
        response = self.generate_response(query_text, relevant_docs)
        
        return {
            **response,
            'retrieved_documents': len(relevant_docs),
            'query': query_text
        }