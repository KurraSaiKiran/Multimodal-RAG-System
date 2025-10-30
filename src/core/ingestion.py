"""
Document ingestion pipeline
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.processors.text_processor import TextProcessor
from src.processors.image_processor import ImageProcessor
from src.processors.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.utils.logger import setup_logger, log_execution_time
from src.utils.helpers import get_file_type, validate_file

logger = setup_logger(__name__)


class IngestionPipeline:
    """
    Pipeline for ingesting documents into the vector store
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize ingestion pipeline
        
        Args:
            vector_store: Optional vector store instance
        """
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()
        self.vector_store = vector_store or VectorStore()
        
        logger.info("IngestionPipeline initialized")
    
    @log_execution_time
    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a single file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Validate file
            is_valid, error_msg = validate_file(file_path)
            if not is_valid:
                raise ValueError(f"File validation failed: {error_msg}")
            
            # Determine file type and process
            file_type = get_file_type(file_path)
            logger.info(f"Processing {file_type} file: {Path(file_path).name}")
            
            if file_type == "text":
                processed_data = self.text_processor.process_text_file(file_path)
            elif file_type == "image":
                processed_data = self.image_processor.process_image(file_path)
                # Convert to expected format
                processed_data["chunks"] = [processed_data["text"]]
            elif file_type == "pdf":
                processed_data = self.pdf_processor.process_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Add to vector store
            doc_ids = self._add_to_vector_store(processed_data)
            
            result = {
                "success": True,
                "file_path": file_path,
                "file_type": file_type,
                "chunks_created": len(doc_ids),
                "document_ids": doc_ids
            }
            
            logger.info(f"Successfully ingested {file_path} ({len(doc_ids)} chunks)")
            return result
        
        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {str(e)}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    def _add_to_vector_store(self, processed_data: Dict[str, Any]) -> List[str]:
        """
        Add processed data to vector store
        
        Args:
            processed_data: Processed document data
            
        Returns:
            List of document IDs
        """
        chunks = processed_data.get("chunks", [])
        metadata = processed_data.get("metadata", {})
        
        # Create metadata for each chunk
        metadatas = []
        for idx, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = idx
            chunk_metadata["total_chunks"] = len(chunks)
            metadatas.append(chunk_metadata)
        
        # Add to vector store
        doc_ids = self.vector_store.add_documents(
            texts=chunks,
            metadatas=metadatas
        )
        
        return doc_ids
    
    @log_execution_time
    def ingest_multiple_files(self, file_paths: List[str], parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Ingest multiple files
        
        Args:
            file_paths: List of file paths
            parallel: Whether to process files in parallel
            
        Returns:
            List of ingestion results
        """
        if parallel:
            return self._ingest_parallel(file_paths)
        else:
            results = []
            for file_path in file_paths:
                result = self.ingest_file(file_path)
                results.append(result)
            return results
    
    def _ingest_parallel(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Ingest files in parallel using ThreadPoolExecutor
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of ingestion results
        """
        from src.config import Config
        
        results = []
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            future_to_file = {executor.submit(self.ingest_file, fp): fp for fp in file_paths}
            
            for future in future_to_file:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    results.append({
                        "success": False,
                        "file_path": file_path,
                        "error": str(e)
                    })
        
        successful = sum(1 for r in results if r.get("success", False))
        logger.info(f"Ingested {successful}/{len(file_paths)} files successfully")
        return results
    
    @log_execution_time
    async def ingest_file_async(self, file_path: str) -> Dict[str, Any]:
        """
        Asynchronously ingest a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with ingestion results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ingest_file, file_path)
    
    async def ingest_multiple_files_async(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Asynchronously ingest multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of ingestion results
        """
        tasks = [self.ingest_file_async(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {file_paths[idx]}: {str(result)}")
                processed_results.append({
                    "success": False,
                    "file_path": file_paths[idx],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get ingestion statistics
        
        Returns:
            Dictionary with statistics
        """
        return self.vector_store.get_collection_stats()
