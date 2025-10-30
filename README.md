# Multimodal RAG System

A Retrieval-Augmented Generation system that processes and queries multiple data formats including images, text documents, and PDFs with mixed content.

## 🚀 Features

- **Multimodal Document Processing**: Supports text files, images (PNG, JPG, JPEG), and PDFs
- **Intelligent Query Classification**: Automatically classifies queries as factual, exploratory, or cross-modal
- **Vector Storage**: Uses ChromaDB for efficient similarity search
- **Modern Web Interface**: Drag-and-drop upload with real-time feedback
- **RESTful API**: Flask-based API with comprehensive endpoints
- **Async Processing**: Concurrent document processing for better performance

## 🏗️ Architecture

```
├── backend/              # Backend API server
│   ├── app.py           # Flask REST API
│   ├── config.py        # Configuration settings
│   ├── core/            # Core system components
│   │   ├── embeddings.py     # Sentence transformer embeddings
│   │   ├── vector_store.py   # ChromaDB integration
│   │   ├── document_processor.py  # Document processing coordinator
│   │   └── query_engine.py   # Query processing and response generation
│   └── utils/           # Utility modules
│       ├── text_processor.py # Text cleaning and chunking
│       ├── image_processor.py # Image processing
│       └── pdf_processor.py  # PDF text and image extraction
├── frontend/            # Modern web interface
│   ├── index.html       # Main HTML page
│   ├── style.css        # Modern CSS styling
│   ├── script.js        # Interactive JavaScript
│   └── server.py        # Frontend server
├── start_backend.py     # Backend startup script
├── start_frontend.py    # Frontend startup script
└── test_api.py          # System test script
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multimodal-rag-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   CHROMA_DB_PATH=chroma_db
   UPLOAD_FOLDER=uploads
   MAX_CONTENT_LENGTH=16777216
   ```

5. **Run the application**

   **Start Backend (Required):**
   ```bash
   python start_backend.py
   ```
   
   **Start Frontend (Optional - for web UI):**
   ```bash
   # In a new terminal window
   python start_frontend.py
   ```
   
   **Test the system:**
   ```bash
   # In a new terminal window
   python test_api.py
   ```

**Access Points:**
- **Web Interface**: `http://localhost:3000` (Modern UI)
- **Backend API**: `http://localhost:5000` (REST API)

## 📡 API Documentation

### Health Check
```http
GET /api/health
```

### Upload Single Document
```http
POST /api/upload
Content-Type: multipart/form-data

file: <document file>
```

### Upload Multiple Documents
```http
POST /api/upload/batch
Content-Type: multipart/form-data

files: <multiple document files>
```

### Query Documents
```http
POST /api/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "content_type_filter": "text"  // optional: "text", "image", "pdf"
}
```

### Search Documents (No LLM)
```http
POST /api/search
Content-Type: application/json

{
  "query": "machine learning",
  "n_results": 5,
  "content_type_filter": "text"  // optional
}
```

### Get Collection Statistics
```http
GET /api/stats
```

### Delete Document
```http
DELETE /api/documents/<document_id>
```

## 💡 Usage Examples

### Web Interface
1. Go to `http://localhost:3000`
2. Drag and drop files or click to upload
3. Ask questions about your uploaded documents
4. Get intelligent responses with source attribution

### API Usage
```python
import requests

# Upload a document
files = {'files': open('document.pdf', 'rb')}
response = requests.post('http://localhost:5000/api/upload/batch', files=files)

# Query the document
query = {"query": "What is the main topic of this document?"}
response = requests.post('http://localhost:5000/api/query', json=query)
print(response.json()['response'])
```

## 🔧 Technical Details

### Supported File Formats
- **Text**: .txt, .md
- **Images**: .png, .jpg, .jpeg
- **PDFs**: .pdf (with text, images, or mixed content)

### Key Technologies
- **Backend**: Flask, ChromaDB, Sentence Transformers
- **Frontend**: Vanilla JavaScript, Modern CSS
- **AI**: Groq API (Llama 3.1), Sentence Transformers
- **Storage**: ChromaDB vector database

### Performance Features
- Async document processing
- Batch embedding generation
- Intelligent query classification
- Efficient chunking strategies
- Built-in caching

## 🚨 Troubleshooting

### Backend won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is available
- Verify your Groq API key is set in `.env`

### No results from queries
- Upload documents first using the web interface
- Try the "Test System" button to verify functionality
- Run `python test_api.py` to check system status

### Upload fails
- Check file formats (PDF, TXT, MD, PNG, JPG, JPEG only)
- Ensure files are under 16MB
- Check backend logs for detailed error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Groq for LLM API
- Flask for the web framework