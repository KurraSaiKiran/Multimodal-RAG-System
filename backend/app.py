import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from config import Config
from core.document_processor import DocumentProcessor
from core.query_engine import QueryEngine
from core.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

document_processor = DocumentProcessor()
query_engine = QueryEngine()
vector_store = VectorStore()

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    allowed_extensions = {'.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf'}
    return '.' in filename and os.path.splitext(filename)[1].lower() in allowed_extensions

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not supported'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(document_processor.process_document(file_path))
        loop.close()
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'message': 'Document processed successfully',
            'filename': file.filename,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/upload/batch', methods=['POST'])
def upload_multiple_documents():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        file_paths = []
        processed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
                processed_files.append(file.filename)
        
        if not file_paths:
            return jsonify({'error': 'No valid files to process'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            document_processor.process_multiple_documents(file_paths)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(file_paths)} documents',
            'files': processed_files,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}")
        return jsonify({'error': f'Batch upload failed: {str(e)}'}), 500

@app.route('/api/query', methods=['POST'])
def query_documents():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text required'}), 400
        
        query_text = data['query']
        content_type_filter = data.get('content_type_filter')
        
        result = query_engine.query(query_text, content_type_filter)
        
        return jsonify({
            'success': True,
            'query': query_text,
            'response': result['response'],
            'query_type': result['query_type'],
            'sources': result['sources'],
            'retrieved_documents': result['retrieved_documents'],
            'context_used': result.get('context_used', 0)
        })
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def search_documents():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text required'}), 400
        
        query_text = data['query']
        n_results = data.get('n_results', Config.TOP_K)
        content_type_filter = data.get('content_type_filter')
        
        filter_metadata = {}
        if content_type_filter:
            filter_metadata['content_type'] = content_type_filter
        
        results = vector_store.search(
            query=query_text,
            n_results=n_results,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        return jsonify({
            'success': True,
            'query': query_text,
            'results': results,
            'total_results': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = vector_store.get_collection_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/debug/documents', methods=['GET'])
def debug_documents():
    """Debug endpoint to see what documents are in the database"""
    try:
        # Get a sample of documents
        results = vector_store.search("test", n_results=10, filter_metadata=None)
        return jsonify({
            'success': True,
            'total_documents': vector_store.get_collection_stats()['total_documents'],
            'sample_documents': results
        })
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

@app.route('/api/test/add', methods=['POST'])
def test_add_document():
    """Test endpoint to add a simple document"""
    try:
        test_doc = {
            'content': 'This is a test document about machine learning and artificial intelligence.',
            'metadata': {
                'source': 'test.txt',
                'content_type': 'text',
                'file_type': 'txt'
            }
        }
        
        doc_ids = vector_store.add_documents([test_doc])
        
        return jsonify({
            'success': True,
            'message': 'Test document added',
            'document_ids': doc_ids
        })
    except Exception as e:
        logger.error(f"Test add error: {str(e)}")
        return jsonify({'error': f'Test add failed: {str(e)}'}), 500

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        success = vector_store.delete_documents([doc_id])
        if success:
            return jsonify({
                'success': True,
                'message': f'Document {doc_id} deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete document'}), 500
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)