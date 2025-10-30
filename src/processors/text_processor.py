"""
Text document processor
"""
from typing import Dict, Any, List
from pathlib import Path
from src.config import Config
from src.utils.logger import setup_logger, log_execution_time
from src.utils.helpers import create_metadata, chunk_text

logger = setup_logger(__name__)


class TextProcessor:
    """
    Process plain text documents
    """
    
    def __init__(self):
        """Initialize text processor"""
        logger.info("TextProcessor initialized")
    
    @log_execution_time
    def process_text_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Dictionary with processed text data
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create chunks
            chunks = chunk_text(content, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
            
            # Create metadata
            metadata = create_metadata(file_path, chunk_count=len(chunks))
            
            result = {
                "text": content,
                "chunks": chunks,
                "metadata": metadata,
                "file_path": file_path
            }
            
            logger.info(f"Processed text file: {Path(file_path).name} ({len(chunks)} chunks)")
            return result
        
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            raise
    
    @log_execution_time
    def process_text(self, text: str, source_name: str = "direct_input") -> Dict[str, Any]:
        """
        Process raw text directly
        
        Args:
            text: Text content
            source_name: Name/identifier for the source
            
        Returns:
            Dictionary with processed text data
        """
        try:
            # Create chunks
            chunks = chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
            
            # Create basic metadata
            metadata = {
                "source": source_name,
                "file_type": "text",
                "chunk_count": len(chunks),
                "text_length": len(text)
            }
            
            result = {
                "text": text,
                "chunks": chunks,
                "metadata": metadata
            }
            
            logger.info(f"Processed text from {source_name} ({len(chunks)} chunks)")
            return result
        
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    def process_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple text files
        
        Args:
            file_paths: List of text file paths
            
        Returns:
            List of processed text data
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process_text_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(results)}/{len(file_paths)} text files successfully")
        return results
