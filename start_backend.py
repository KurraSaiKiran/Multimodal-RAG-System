#!/usr/bin/env python3
"""
Start the backend server
"""

import os
import sys
from pathlib import Path

def main():
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('chroma_db', exist_ok=True)
    
    # Add backend to Python path
    backend_path = project_root / 'backend'
    sys.path.insert(0, str(backend_path))
    
    print("Starting Multimodal RAG Backend...")
    print("Backend API: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    # Change to backend directory and run
    os.chdir(backend_path)
    
    try:
        from app import app
        app.run(debug=False, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\nBackend stopped.")
    except Exception as e:
        print(f"Error starting backend: {e}")

if __name__ == '__main__':
    main()