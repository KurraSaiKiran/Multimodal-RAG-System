from PIL import Image
from typing import Dict, Any
import os

class ImageProcessor:
    def __init__(self):
        self.model_loaded = False
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract descriptive text from image"""
        filename = os.path.basename(image_path)
        
        try:
            # Get basic image info
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                
            return f"Image file: {filename} ({format_name}, {width}x{height}). This is an uploaded image file that can be referenced in queries."
        except Exception as e:
            return f"Image file: {filename}. Could not process image: {str(e)}"
    
    def preprocess_image(self, image_path: str) -> Dict[str, Any]:
        """Preprocess image and extract metadata"""
        try:
            # Extract image description
            description = self.extract_text_from_image(image_path)
            
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            return {
                'description': description,
                'width': width,
                'height': height,
                'file_path': image_path
            }
        except Exception as e:
            return {
                'description': f"Error processing image: {str(e)}",
                'file_path': image_path
            }