#!/usr/bin/env python3
"""
Start the frontend server
"""

import os
import sys
import webbrowser
from pathlib import Path
import http.server
import socketserver

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)
    
    port = 3000
    
    print("Starting Multimodal RAG Frontend...")
    print(f"Frontend UI: http://localhost:{port}")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    # Create server
    with socketserver.TCPServer(("127.0.0.1", port), CustomHTTPRequestHandler) as httpd:
        # Open browser
        webbrowser.open(f'http://localhost:{port}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nFrontend stopped.")

if __name__ == "__main__":
    main()