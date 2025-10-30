import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', str(project_root / 'chroma_db'))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(project_root / 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # Model configurations
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    VISION_MODEL = 'blip-image-captioning-base'
    
    # Chunking parameters
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Retrieval parameters
    TOP_K = 5
    SIMILARITY_THRESHOLD = 0.3