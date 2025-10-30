import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Tuple
from utils.text_processor import TextProcessor
from utils.image_processor import ImageProcessor
from utils.pdf_processor import PDFProcessor
from .vector_store import VectorStore

class DocumentProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore()
        
        self.supported_formats = {
            'text': ['.txt', '.md'],
            'image': ['.png', '.jpg', '.jpeg'],
            'pdf': ['.pdf']
        }
    
    def get_file_type(self, file_path: str) -> str:
        """Determine file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document and add to vector store"""
        file_type = self.get_file_type(file_path)
        
        if file_type == 'unknown':
            return {'error': f'Unsupported file type: {file_path}'}
        
        try:
            base_metadata = {
                'source': file_path,
                'file_type': file_type,
                'upload_timestamp': datetime.now().isoformat(),
                'filename': os.path.basename(file_path)
            }
            
            if file_type == 'text':
                return await self._process_text_file(file_path, base_metadata)
            elif file_type == 'image':
                return await self._process_image_file(file_path, base_metadata)
            elif file_type == 'pdf':
                return await self._process_pdf_file(file_path, base_metadata)
                
        except Exception as e:
            return {'error': f'Error processing {file_path}: {str(e)}'}
    
    async def _process_text_file(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata['content_type'] = 'text'
        chunks = self.text_processor.chunk_text(content, metadata)
        
        if chunks:
            doc_ids = self.vector_store.add_documents(chunks)
            return {
                'success': True,
                'file_path': file_path,
                'chunks_created': len(chunks),
                'document_ids': doc_ids
            }
        
        return {'error': 'No content to process'}
    
    async def _process_image_file(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process image file"""
        img_info = self.image_processor.preprocess_image(file_path)
        
        metadata.update({
            'content_type': 'image',
            'width': img_info.get('width'),
            'height': img_info.get('height')
        })
        
        document = {
            'content': img_info['description'],
            'metadata': metadata
        }
        
        doc_ids = self.vector_store.add_documents([document])
        
        return {
            'success': True,
            'file_path': file_path,
            'description': img_info['description'],
            'document_ids': doc_ids
        }
    
    async def _process_pdf_file(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF file"""
        text_chunks, image_data = self.pdf_processor.extract_text_and_images(file_path)
        
        all_documents = []
        all_documents.extend(text_chunks)
        
        # Process images from PDF
        for img_info in image_data:
            img_doc = {
                'content': img_info['description'],
                'metadata': {**metadata, **img_info['metadata']}
            }
            all_documents.append(img_doc)
        
        if all_documents:
            doc_ids = self.vector_store.add_documents(all_documents)
            return {
                'success': True,
                'file_path': file_path,
                'text_chunks': len(text_chunks),
                'images_processed': len(image_data),
                'total_documents': len(all_documents),
                'document_ids': doc_ids
            }
        
        return {'error': 'No content extracted from PDF'}
    
    async def process_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple documents concurrently"""
        tasks = [self.process_document(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results