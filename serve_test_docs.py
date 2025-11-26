#!/usr/bin/env python3
"""
Simple HTTP server for OLI test documents.
Serves files from test_documents/ directory with CORS enabled.

Usage:
    python serve_test_docs.py
    
Then open: http://localhost:8080
"""

import http.server
import socketserver
import os
from functools import partial

PORT = 8080
DIRECTORY = "test_documents"

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS support for PDF.js"""
    
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for PDF.js
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')
        self.send_header('Access-Control-Expose-Headers', 'Content-Length, Content-Range')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()

def main():
    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if test_documents exists
    if not os.path.exists(DIRECTORY):
        print(f"[!] Directory '{DIRECTORY}' not found!")
        print(f"    Run 'python create_test_pdf.py' first to generate test documents.")
        return
    
    handler = partial(CORSHTTPRequestHandler, directory=DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"")
        print(f"  OLI Test Documents Server")
        print(f"  =========================")
        print(f"")
        print(f"  Serving '{DIRECTORY}/' at:")
        print(f"")
        print(f"    -> http://localhost:{PORT}/")
        print(f"")
        print(f"  Available files:")
        for f in os.listdir(DIRECTORY):
            print(f"    - http://localhost:{PORT}/{f}")
        print(f"")
        print(f"  Press Ctrl+C to stop")
        print(f"")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")

if __name__ == "__main__":
    main()

