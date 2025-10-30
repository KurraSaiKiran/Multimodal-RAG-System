"""
Unit tests for utility functions
"""
import pytest
import os
import tempfile
from pathlib import Path
from src.utils.helpers import (
    get_file_hash,
    get_file_type,
    validate_file,
    create_metadata,
    chunk_text,
    sanitize_filename
)


class TestHelpers:
    """Test utility helper functions"""
    
    def test_get_file_type(self):
        """Test file type detection"""
        assert get_file_type("test.txt") == "text"
        assert get_file_type("test.pdf") == "pdf"
        assert get_file_type("test.png") == "image"
        assert get_file_type("test.jpg") == "image"
        assert get_file_type("test.jpeg") == "image"
        assert get_file_type("test.unknown") == "unknown"
    
    def test_get_file_hash(self, tmp_path):
        """Test file hash generation"""
        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = get_file_hash(str(test_file))
        assert len(hash1) == 64  # SHA256 hash length
        
        # Same content should produce same hash
        hash2 = get_file_hash(str(test_file))
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash3 = get_file_hash(str(test_file))
        assert hash1 != hash3
    
    def test_validate_file(self, tmp_path):
        """Test file validation"""
        # Create a valid file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        is_valid, error = validate_file(str(test_file))
        assert is_valid is True
        assert error is None
        
        # Test non-existent file
        is_valid, error = validate_file("nonexistent.txt")
        assert is_valid is False
        assert "does not exist" in error
    
    def test_chunk_text(self):
        """Test text chunking"""
        text = "This is a test. " * 100
        
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        
        # Check that chunks have some overlap
        for i in range(len(chunks) - 1):
            assert len(chunks[i]) > 0
        
        # Short text should return single chunk
        short_text = "Short text"
        chunks = chunk_text(short_text, chunk_size=100, overlap=20)
        assert len(chunks) == 1
        assert chunks[0] == short_text
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("../../../etc/passwd") == ".._.._.._.._etc_passwd"
        assert sanitize_filename("test:file.txt") == "test_file.txt"
        assert sanitize_filename("test*file?.txt") == "test_file_.txt"
    
    def test_create_metadata(self, tmp_path):
        """Test metadata creation"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        metadata = create_metadata(str(test_file), custom_field="custom_value")
        
        assert "file_name" in metadata
        assert "file_path" in metadata
        assert "file_type" in metadata
        assert "file_size" in metadata
        assert "file_hash" in metadata
        assert "upload_timestamp" in metadata
        assert metadata["custom_field"] == "custom_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
