"""
Configuration management for the Multimodal RAG System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    CACHE_DIR = os.getenv('CACHE_DIR', './cache')
    LOG_DIR = Path('./logs')
    
    # Grok API
    GROK_API_KEY = os.getenv('GROK_API_KEY', '')
    GROK_API_BASE = os.getenv('GROK_API_BASE', 'https://api.x.ai/v1')
    
    # Vector Database
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
    
    # Models
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    VISION_MODEL = os.getenv('VISION_MODEL', 'Salesforce/blip-image-captioning-base')
    
    # Text Processing
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 512))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
    
    # Upload Settings
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 50000000))  # 50MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}
    
    # Cache
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    QUERY_TIMEOUT = int(os.getenv('QUERY_TIMEOUT', 30))
    
    # LangSmith Tracing
    LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY', '')
    LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT', 'multimodal-rag')
    
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        for directory in [cls.UPLOAD_FOLDER, cls.CACHE_DIR, cls.LOG_DIR, cls.CHROMA_PERSIST_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GROK_API_KEY:
            raise ValueError("GROK_API_KEY is required. Please set it in .env file")
        return True
