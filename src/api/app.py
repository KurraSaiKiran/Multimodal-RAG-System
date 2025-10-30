"""
Flask application factory
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.api.routes import api_bp
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app():
    """
    Create and configure Flask application
    
    Returns:
        Configured Flask app
    """
    app = Flask(__name__, 
                static_folder='../../static',
                template_folder='../../templates')
    
    # Configure app
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize directories
    Config.init_app()
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Root route
    @app.route('/')
    def index():
        """Serve frontend"""
        from flask import render_template
        try:
            return render_template('index.html')
        except Exception:
            return {
                "name": "Multimodal RAG System",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/api/health",
                    "upload": "/api/upload",
                    "batch_upload": "/api/upload/batch",
                    "query": "/api/query",
                    "answer": "/api/answer",
                    "stats": "/api/stats",
                    "documents": "/api/documents"
                }
            }
    
    # Static files route
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files"""
        return send_from_directory(app.static_folder, filename)
    
    logger.info("Flask application created successfully")
    return app
