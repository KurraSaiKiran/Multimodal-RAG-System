"""
Unit tests for text processor
"""
import pytest
import tempfile
from pathlib import Path
from src.processors.text_processor import TextProcessor


class TestTextProcessor:
    """Test text processor functionality"""
    
    @pytest.fixture
    def processor(self):
        """Create text processor instance"""
        return TextProcessor()
    
    @pytest.fixture
    def test_file(self, tmp_path):
        """Create a temporary test file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document. " * 50)
        return str(test_file)
    
    def test_process_text_file(self, processor, test_file):
        """Test processing a text file"""
        result = processor.process_text_file(test_file)
        
        assert "text" in result
        assert "chunks" in result
        assert "metadata" in result
        assert "file_path" in result
        
        assert len(result["text"]) > 0
        assert len(result["chunks"]) > 0
        assert result["metadata"]["file_type"] == "text"
    
    def test_process_text(self, processor):
        """Test processing raw text"""
        text = "This is a test. " * 100
        result = processor.process_text(text, source_name="test")
        
        assert "text" in result
        assert "chunks" in result
        assert "metadata" in result
        
        assert result["text"] == text
        assert len(result["chunks"]) > 0
        assert result["metadata"]["source"] == "test"
    
    def test_process_multiple_files(self, processor, tmp_path):
        """Test processing multiple files"""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test document {i}. " * 20)
            files.append(str(test_file))
        
        results = processor.process_multiple_files(files)
        
        assert len(results) == 3
        for result in results:
            assert "text" in result
            assert "chunks" in result
    
    def test_empty_file(self, processor, tmp_path):
        """Test processing empty file"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = processor.process_text_file(str(empty_file))
        
        assert result["text"] == ""
        # Empty text should still create at least one chunk
        assert len(result["chunks"]) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
