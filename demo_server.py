"""
AI SDR Platform - Demo Frontend Server

Run this to serve the demo landing page on port 3000.
The frontend connects to the API at localhost:8000.

Usage:
    python demo_server.py

Then open: http://localhost:3000
"""

import http.server
import socketserver
import os
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🚀 AI SDR Platform - Demo Frontend                                  ║
║                                                                       ║
║   Starting server on http://localhost:{}                            ║
║                                                                       ║
║   Make sure the API is running:                                       ║
║   uvicorn api.app:app --reload --port 8000                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """.format(PORT))
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)


if __name__ == "__main__":
    main()
