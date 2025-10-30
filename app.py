"""
Main entry point for the Multimodal RAG System
"""
from src.api.app import create_app
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Start the Flask application"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create app
        app = create_app()
        
        logger.info("=" * 60)
        logger.info("Multimodal RAG System Starting")
        logger.info("=" * 60)
        logger.info(f"Host: {Config.HOST}")
        logger.info(f"Port: {Config.PORT}")
        logger.info(f"Debug: {Config.FLASK_DEBUG}")
        logger.info(f"Vector Store: {Config.CHROMA_PERSIST_DIR}")
        logger.info("=" * 60)
        
        # Run app
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.FLASK_DEBUG,
            threaded=True
        )
    
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise


if __name__ == "__main__":
    main()
