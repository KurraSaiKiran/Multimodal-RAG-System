"""
Image processor with vision model integration
"""
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from typing import Dict, Any, List
import io
import base64
from pathlib import Path
from src.config import Config
from src.utils.logger import setup_logger, log_execution_time
from src.utils.helpers import create_metadata, get_file_hash

logger = setup_logger(__name__)


class ImageProcessor:
    """
    Process images and extract descriptions using vision models
    """
    
    def __init__(self):
        """Initialize image processor with vision model"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing ImageProcessor on device: {self.device}")
        
        # Load vision model
        try:
            self.processor = BlipProcessor.from_pretrained(Config.VISION_MODEL)
            self.model = BlipForConditionalGeneration.from_pretrained(Config.VISION_MODEL)
            self.model.to(self.device)
            logger.info(f"Loaded vision model: {Config.VISION_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load vision model: {str(e)}")
            raise
    
    @log_execution_time
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process a single image and extract description
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image data and description
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Generate description
            description = self._generate_description(image)
            
            # Generate detailed description (conditional)
            detailed_description = self._generate_detailed_description(image)
            
            # Create metadata
            metadata = create_metadata(
                image_path,
                description=description,
                detailed_description=detailed_description,
                image_size=image.size,
                image_mode=image.mode
            )
            
            # Combine descriptions for embedding
            combined_text = f"{description}. {detailed_description}"
            
            result = {
                "text": combined_text,
                "description": description,
                "detailed_description": detailed_description,
                "metadata": metadata,
                "image_path": image_path
            }
            
            logger.info(f"Processed image: {Path(image_path).name}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    def _generate_description(self, image: Image.Image) -> str:
        """
        Generate a brief description of the image
        
        Args:
            image: PIL Image object
            
        Returns:
            Image description
        """
        try:
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_new_tokens=50)
            description = self.processor.decode(out[0], skip_special_tokens=True)
            return description.strip()
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            return "Image description unavailable"
    
    def _generate_detailed_description(self, image: Image.Image) -> str:
        """
        Generate a more detailed description of the image
        
        Args:
            image: PIL Image object
            
        Returns:
            Detailed image description
        """
        try:
            # Use conditional generation for more details
            text = "a detailed description of"
            inputs = self.processor(image, text, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_new_tokens=100)
            description = self.processor.decode(out[0], skip_special_tokens=True)
            return description.strip()
        except Exception as e:
            logger.error(f"Error generating detailed description: {str(e)}")
            return ""
    
    @log_execution_time
    def process_multiple_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple images
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of processed image data
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.process_image(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(results)}/{len(image_paths)} images successfully")
        return results
    
    def image_to_base64(self, image_path: str) -> str:
        """
        Convert image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            raise
    
    def validate_image(self, image_path: str) -> bool:
        """
        Validate if file is a valid image
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
