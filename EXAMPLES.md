# Example Usage Scripts

This document provides Python code examples for using the RAG system programmatically.

## Basic Document Ingestion

```python
from src.core.ingestion import IngestionPipeline
from src.core.vector_store import VectorStore

# Initialize
vector_store = VectorStore()
pipeline = IngestionPipeline(vector_store)

# Ingest a single file
result = pipeline.ingest_file("path/to/document.pdf")
print(f"Processed: {result['chunks_created']} chunks")

# Ingest multiple files
files = ["doc1.pdf", "doc2.txt", "image.png"]
results = pipeline.ingest_multiple_files(files, parallel=True)
print(f"Processed {len(results)} files")
```

## Querying Documents

```python
from src.core.retrieval import RetrievalEngine

# Initialize
engine = RetrievalEngine()

# Simple semantic search
results = engine.retrieve(
    query="What is machine learning?",
    n_results=5,
    strategy="semantic"
)

# Hybrid search with reranking
results = engine.retrieve(
    query="explain neural networks",
    n_results=10,
    strategy="hybrid"
)
reranked = engine.rerank_results("explain neural networks", results, top_k=5)

# Get AI-generated answer
answer_data = engine.answer_query(
    query="What are the main topics discussed?",
    n_results=5
)
print(answer_data['answer'])
```

## Custom Processing

```python
from src.processors.text_processor import TextProcessor
from src.processors.image_processor import ImageProcessor
from src.processors.pdf_processor import PDFProcessor

# Process text
text_proc = TextProcessor()
result = text_proc.process_text(
    "Your text content here",
    source_name="custom_source"
)

# Process image
image_proc = ImageProcessor()
result = image_proc.process_image("path/to/image.jpg")
print(result['description'])

# Process PDF
pdf_proc = PDFProcessor()
result = pdf_proc.process_pdf("path/to/document.pdf")
print(f"PDF Type: {result['type']}")
print(f"Chunks: {len(result['chunks'])}")
```

## Direct Embedding Generation

```python
from src.core.embeddings import EmbeddingService

# Initialize
embedding_service = EmbeddingService(use_grok=True)

# Generate embeddings
texts = ["text 1", "text 2", "text 3"]
embeddings = embedding_service.embed_text(texts)

# Calculate similarity
similarity = embedding_service.similarity(embeddings[0], embeddings[1])
print(f"Similarity: {similarity}")
```

## Async Processing

```python
import asyncio
from src.core.ingestion import IngestionPipeline

async def process_documents():
    pipeline = IngestionPipeline()
    
    files = ["doc1.pdf", "doc2.txt", "doc3.pdf"]
    results = await pipeline.ingest_multiple_files_async(files)
    
    for result in results:
        if result['success']:
            print(f"✓ {result['file_path']}")
        else:
            print(f"✗ {result['file_path']}: {result['error']}")

# Run
asyncio.run(process_documents())
```

## Custom Metadata Filtering

```python
from src.core.retrieval import RetrievalEngine

engine = RetrievalEngine()

# Query with metadata filter
results = engine.retrieve(
    query="machine learning",
    n_results=5,
    strategy="semantic",
    filter_dict={
        "file_type": "pdf",
        # Add other metadata filters
    }
)
```

## Working with Cache

```python
from src.core.retrieval import RetrievalEngine

engine = RetrievalEngine()

# First query (will be cached)
results1 = engine.retrieve(query="AI concepts", n_results=5)

# Same query (will use cache)
results2 = engine.retrieve(query="AI concepts", n_results=5)

# Clear cache
engine.clear_cache()
```

## Error Handling

```python
from src.core.ingestion import IngestionPipeline
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
pipeline = IngestionPipeline()

try:
    result = pipeline.ingest_file("document.pdf")
    if result['success']:
        logger.info(f"Success: {result['chunks_created']} chunks")
    else:
        logger.error(f"Failed: {result['error']}")
except Exception as e:
    logger.error(f"Exception: {str(e)}")
```
