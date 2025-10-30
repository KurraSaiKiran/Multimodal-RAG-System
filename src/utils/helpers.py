"""
Helper utilities for file handling, validation, and common operations
"""
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from src.config import Config


def get_file_hash(file_path: str) -> str:
    """
    Generate SHA256 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_type(file_path: str) -> str:
    """
    Determine file type from extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type string (text, image, pdf, etc.)
    """
    ext = Path(file_path).suffix.lower().lstrip('.')
    
    type_mapping = {
        'txt': 'text',
        'pdf': 'pdf',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'docx': 'document',
        'xlsx': 'spreadsheet'
    }
    
    return type_mapping.get(ext, 'unknown')


def get_mime_type(file_path: str) -> str:
    """
    Get MIME type of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'


def validate_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate if file exists and is within size limits
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, "File does not exist"
    
    if not path.is_file():
        return False, "Path is not a file"
    
    file_size = path.stat().st_size
    if file_size > Config.MAX_UPLOAD_SIZE:
        return False, f"File size ({file_size} bytes) exceeds maximum allowed ({Config.MAX_UPLOAD_SIZE} bytes)"
    
    ext = path.suffix.lower().lstrip('.')
    if ext not in Config.ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} not allowed. Allowed types: {Config.ALLOWED_EXTENSIONS}"
    
    return True, None


def create_metadata(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Create metadata dictionary for a document
    
    Args:
        file_path: Path to the file
        **kwargs: Additional metadata fields
        
    Returns:
        Metadata dictionary
    """
    path = Path(file_path)
    
    metadata = {
        'file_name': path.name,
        'file_path': str(path.absolute()),
        'file_type': get_file_type(file_path),
        'file_size': path.stat().st_size,
        'mime_type': get_mime_type(file_path),
        'file_hash': get_file_hash(file_path),
        'upload_timestamp': datetime.utcnow().isoformat(),
        'processed_timestamp': datetime.utcnow().isoformat()
    }
    
    # Add any additional metadata
    metadata.update(kwargs)
    
    return metadata


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Number of overlapping characters
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = Config.CHUNK_SIZE
    if overlap is None:
        overlap = Config.CHUNK_OVERLAP
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for char in ['. ', '! ', '? ', '\n\n']:
                last_break = text[start:end].rfind(char)
                if last_break != -1:
                    end = start + last_break + len(char)
                    break
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Remove or replace dangerous characters
    dangerous_chars = ['..', '/', '\\', '\0', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename
