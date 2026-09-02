#!/usr/bin/env python3
"""
Standalone Frontend Web Server for PHI/PII De-Identification Gateway.
Serves static UI files on port 3000 and connects to the Backend API on port 8000.
"""

import http.server
import os
import socketserver
import sys

PORT = int(os.environ.get("FRONTEND_PORT", 3000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local testing
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Clean formatted server logs
        sys.stdout.write(f"[FRONTEND :3000] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_frontend(port: int = PORT):
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        print("=" * 75)
        print("  PHI/PII DE-IDENTIFICATION GATEWAY — STANDALONE WEB FRONTEND")
        print(f"  Serving on: http://localhost:{port}")
        print("  Backend API expected on: http://localhost:8000")
        print("=" * 75)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[FRONTEND] Server stopped gracefully.")


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_frontend(port_arg)
