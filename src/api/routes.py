"""
Flask API routes for the Multimodal RAG System
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from typing import Dict, Any
from src.core.ingestion import IngestionPipeline
from src.core.retrieval import RetrievalEngine
from src.core.vector_store import VectorStore
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import sanitize_filename, validate_file

logger = setup_logger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
vector_store = VectorStore()
ingestion_pipeline = IngestionPipeline(vector_store)
retrieval_engine = RetrievalEngine(vector_store)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        stats = vector_store.get_collection_stats()
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "vector_store": stats
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


@api_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    Upload and process a document
    
    Request:
        - file: Document file (multipart/form-data)
    
    Response:
        - success: Boolean
        - message: Status message
        - data: Ingestion results
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Sanitize filename
        filename = sanitize_filename(file.filename)
        
        # Save file
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        logger.info(f"File uploaded: {filename}")
        
        # Validate file
        is_valid, error_msg = validate_file(file_path)
        if not is_valid:
            os.remove(file_path)
            return jsonify({
                "success": False,
                "error": error_msg
            }), 400
        
        # Process and ingest file
        result = ingestion_pipeline.ingest_file(file_path)
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "message": "Document uploaded and processed successfully",
                "data": result
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Processing failed")
            }), 500
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/upload/batch', methods=['POST'])
def upload_batch():
    """
    Upload and process multiple documents
    
    Request:
        - files: Multiple document files (multipart/form-data)
        - parallel: Whether to process in parallel (optional, default: true)
    
    Response:
        - success: Boolean
        - message: Status message
        - data: List of ingestion results
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({
                "success": False,
                "error": "No files provided"
            }), 400
        
        files = request.files.getlist('files')
        parallel = request.form.get('parallel', 'true').lower() == 'true'
        
        # Save all files
        file_paths = []
        for file in files:
            if file.filename:
                filename = sanitize_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        logger.info(f"Batch upload: {len(file_paths)} files")
        
        # Process files
        results = ingestion_pipeline.ingest_multiple_files(file_paths, parallel=parallel)
        
        successful = sum(1 for r in results if r.get("success", False))
        
        return jsonify({
            "success": True,
            "message": f"Processed {successful}/{len(results)} files successfully",
            "data": results
        }), 201
    
    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/query', methods=['POST'])
def query_documents():
    """
    Query the document store
    
    Request JSON:
        - query: Query string (required)
        - n_results: Number of results (optional, default: 5)
        - strategy: Retrieval strategy (optional, default: 'semantic')
                   Options: 'semantic', 'hybrid', 'expanded'
        - rerank: Whether to rerank results (optional, default: false)
        - filter: Metadata filter (optional)
    
    Response:
        - success: Boolean
        - query: Original query
        - results: Retrieved documents with metadata and scores
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        query = data['query']
        n_results = data.get('n_results', 5)
        strategy = data.get('strategy', 'semantic')
        rerank = data.get('rerank', False)
        filter_dict = data.get('filter', None)
        
        logger.info(f"Query received: {query[:50]}... (strategy: {strategy})")
        
        # Retrieve documents
        results = retrieval_engine.retrieve(
            query=query,
            n_results=n_results,
            strategy=strategy,
            filter_dict=filter_dict
        )
        
        # Rerank if requested
        if rerank and results.get('documents'):
            results = retrieval_engine.rerank_results(query, results, top_k=n_results)
        
        return jsonify({
            "success": True,
            "query": query,
            "strategy": strategy,
            "results": {
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "relevance_scores": results.get("relevance_scores", []),
                "ids": results.get("ids", [])
            },
            "count": len(results.get("documents", []))
        }), 200
    
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/answer', methods=['POST'])
def answer_question():
    """
    Get an answer to a question using RAG
    
    Request JSON:
        - query: Question string (required)
        - n_results: Number of context documents (optional, default: 5)
    
    Response:
        - success: Boolean
        - query: Original query
        - answer: Generated answer
        - sources: Source documents used
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        query = data['query']
        n_results = data.get('n_results', 5)
        
        logger.info(f"Answer request: {query[:50]}...")
        
        # Get answer
        result = retrieval_engine.answer_query(query, n_results=n_results)
        
        return jsonify({
            "success": True,
            "query": query,
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "metadatas": result.get("metadatas", []),
            "relevance_scores": result.get("relevance_scores", [])
        }), 200
    
    except Exception as e:
        logger.error(f"Answer generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = ingestion_pipeline.get_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the retrieval cache"""
    try:
        retrieval_engine.clear_cache()
        
        return jsonify({
            "success": True,
            "message": "Cache cleared successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    try:
        upload_dir = Path(Config.UPLOAD_FOLDER)
        documents = []
        
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                documents.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return jsonify({
            "success": True,
            "count": len(documents),
            "documents": documents
        }), 200
    
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        "success": False,
        "error": "File too large"
    }), 413


@api_bp.errorhandler(404)
def not_found(error):
    """Handle not found error"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500
