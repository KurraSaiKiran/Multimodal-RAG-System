import PyPDF2
import io
from PIL import Image
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF for better PDF handling
from .image_processor import ImageProcessor
from .text_processor import TextProcessor

class PDFProcessor:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.text_processor = TextProcessor()
    
    def extract_text_and_images(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract both text and images from PDF"""
        text_chunks = []
        image_data = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                text = page.get_text()
                if text.strip():
                    metadata = {
                        'source': pdf_path,
                        'page_number': page_num + 1,
                        'content_type': 'text',
                        'file_type': 'pdf'
                    }
                    chunks = self.text_processor.chunk_text(text, metadata)
                    text_chunks.extend(chunks)
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_path = f"temp_img_{page_num}_{img_index}.png"
                            
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                            
                            # Process image
                            img_info = self.image_processor.preprocess_image(img_path)
                            img_info['metadata'] = {
                                'source': pdf_path,
                                'page_number': page_num + 1,
                                'image_index': img_index,
                                'content_type': 'image',
                                'file_type': 'pdf_image'
                            }
                            image_data.append(img_info)
                        
                        pix = None
                    except Exception as e:
                        continue
            
            doc.close()
            
        except Exception as e:
            # Fallback to PyPDF2
            text_chunks = self._extract_text_pypdf2(pdf_path)
        
        return text_chunks, image_data
    
    def _extract_text_pypdf2(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Fallback text extraction using PyPDF2"""
        text_chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        metadata = {
                            'source': pdf_path,
                            'page_number': page_num + 1,
                            'content_type': 'text',
                            'file_type': 'pdf'
                        }
                        chunks = self.text_processor.chunk_text(text, metadata)
                        text_chunks.extend(chunks)
        
        except Exception as e:
            pass
        
        return text_chunks