"""
PDF processor for handling text, images, and mixed content
"""
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
from typing import Dict, Any, List, Tuple
from pathlib import Path
import tempfile
import os
from src.config import Config
from src.processors.image_processor import ImageProcessor
from src.processors.text_processor import TextProcessor
from src.utils.logger import setup_logger, log_execution_time
from src.utils.helpers import create_metadata, chunk_text

logger = setup_logger(__name__)


class PDFProcessor:
    """
    Process PDF files containing text, images, or both
    """
    
    def __init__(self):
        """Initialize PDF processor"""
        self.image_processor = ImageProcessor()
        self.text_processor = TextProcessor()
        logger.info("PDFProcessor initialized")
    
    @log_execution_time
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a PDF file and extract all content
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with processed PDF data
        """
        try:
            # Analyze PDF content
            pdf_type = self._analyze_pdf_type(pdf_path)
            logger.info(f"PDF type detected: {pdf_type}")
            
            # Process based on type
            if pdf_type == "text":
                result = self._process_text_pdf(pdf_path)
            elif pdf_type == "image":
                result = self._process_image_pdf(pdf_path)
            else:  # mixed
                result = self._process_mixed_pdf(pdf_path)
            
            # Add metadata
            metadata = create_metadata(pdf_path, pdf_type=pdf_type)
            result["metadata"] = metadata
            
            logger.info(f"Processed PDF: {Path(pdf_path).name}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
    
    def _analyze_pdf_type(self, pdf_path: str) -> str:
        """
        Determine if PDF contains text, images, or both
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDF type: 'text', 'image', or 'mixed'
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                has_text = False
                has_images = False
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        has_text = True
                    
                    if page.images:
                        has_images = True
                    
                    # Early exit if we found both
                    if has_text and has_images:
                        return "mixed"
                
                if has_text and not has_images:
                    return "text"
                elif has_images and not has_text:
                    return "image"
                else:
                    return "mixed"
        
        except Exception as e:
            logger.error(f"Error analyzing PDF type: {str(e)}")
            return "mixed"  # Default to mixed if analysis fails
    
    def _process_text_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with pure text content
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and chunks
        """
        try:
            # Extract text
            text = self._extract_text(pdf_path)
            
            # Create chunks
            chunks = chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
            
            result = {
                "type": "text",
                "text": text,
                "chunks": chunks,
                "images": [],
                "file_path": pdf_path
            }
            
            logger.info(f"Extracted {len(chunks)} text chunks from PDF")
            return result
        
        except Exception as e:
            logger.error(f"Error processing text PDF: {str(e)}")
            raise
    
    def _process_image_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with pure image content
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted images and descriptions
        """
        try:
            # Convert PDF pages to images
            images = self._extract_images_from_pdf(pdf_path)
            
            # Process each image
            image_data = []
            all_text = []
            
            for idx, img_path in enumerate(images):
                img_result = self.image_processor.process_image(img_path)
                img_result["page_number"] = idx + 1
                image_data.append(img_result)
                all_text.append(img_result["text"])
            
            # Combine all descriptions
            combined_text = " ".join(all_text)
            chunks = chunk_text(combined_text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
            
            result = {
                "type": "image",
                "text": combined_text,
                "chunks": chunks,
                "images": image_data,
                "file_path": pdf_path
            }
            
            logger.info(f"Extracted {len(images)} images from PDF")
            return result
        
        except Exception as e:
            logger.error(f"Error processing image PDF: {str(e)}")
            raise
    
    def _process_mixed_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with both text and images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and images
        """
        try:
            # Extract text
            text = self._extract_text(pdf_path)
            
            # Extract images
            images = self._extract_images_from_pdf(pdf_path)
            
            # Process images
            image_data = []
            image_descriptions = []
            
            for idx, img_path in enumerate(images):
                img_result = self.image_processor.process_image(img_path)
                img_result["page_number"] = idx + 1
                image_data.append(img_result)
                image_descriptions.append(img_result["text"])
            
            # Combine text and image descriptions
            combined_text = text
            if image_descriptions:
                combined_text += "\n\nImages in document:\n" + "\n".join(image_descriptions)
            
            chunks = chunk_text(combined_text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
            
            result = {
                "type": "mixed",
                "text": combined_text,
                "chunks": chunks,
                "images": image_data,
                "original_text": text,
                "file_path": pdf_path
            }
            
            logger.info(f"Extracted text and {len(images)} images from PDF")
            return result
        
        except Exception as e:
            logger.error(f"Error processing mixed PDF: {str(e)}")
            raise
    
    def _extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def _extract_images_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extract images from PDF pages
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of paths to extracted images
        """
        try:
            # Create temporary directory for images
            temp_dir = tempfile.mkdtemp()
            image_paths = []
            
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)
            
            for idx, image in enumerate(images):
                img_path = os.path.join(temp_dir, f"page_{idx + 1}.png")
                image.save(img_path, "PNG")
                image_paths.append(img_path)
            
            logger.info(f"Extracted {len(image_paths)} pages as images")
            return image_paths
        
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
            return []
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata = pdf_reader.metadata
                
                return {
                    "page_count": len(pdf_reader.pages),
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", "")
                }
        
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {str(e)}")
            return {}
