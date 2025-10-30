# Quick Start Guide

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Drac AI Task"
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GROK_API_KEY
```

5. **Run the application**
```bash
python app.py
```

6. **Access the web interface**
Open your browser to: http://localhost:5000

## First Steps

### Upload a Document
1. Go to the Upload tab
2. Drag and drop or click to select files
3. Click "Upload Files"
4. Wait for processing to complete

### Query Your Documents
1. Go to the Query tab
2. Enter your search query
3. Select a strategy (semantic, hybrid, or expanded)
4. Optionally enable reranking
5. Click "Search"

### Get AI Answers
1. Go to the Ask Question tab
2. Type your question
3. Click "Get Answer"
4. View the AI-generated answer with source citations

## API Usage Examples

### Upload via API
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf"
```

### Query via API
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "n_results": 5}'
```

### Get Answer via API
```bash
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "your question"}'
```

## Troubleshooting

### Dependencies won't install
- Ensure Python 3.9+ is installed
- Try: `pip install --upgrade pip`
- Install Visual C++ Build Tools (Windows)

### Grok API errors
- Check your API key in .env
- Verify API quota/limits
- System falls back to local models if API fails

### Out of memory
- Reduce batch size
- Use CPU instead of GPU
- Increase system RAM

## Need Help?

See the full README.md for comprehensive documentation.
