#!/usr/bin/env python3
"""
Full Stack Launcher for PHI/PII De-Identification Gateway.
Concurrently launches:
  1. FastAPI Backend API on http://localhost:8000
  2. Standalone Web Frontend on http://localhost:3000
"""

import os
import subprocess
import sys
import time
import webbrowser


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 80)
    print("  STARTING PHI/PII DE-IDENTIFICATION GATEWAY FULL STACK")
    print("  Backend API:  http://localhost:8000  (Swagger: http://localhost:8000/docs)")
    print("  Web Frontend: http://localhost:3000")
    print("=" * 80)

    # Launch Backend Server
    backend_cmd = [sys.executable, "-m", "uvicorn", "deid_gateway.api.server:app", "--host", "127.0.0.1", "--port", "8000"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)

    # Launch Frontend Server
    frontend_cmd = [sys.executable, os.path.join(frontend_dir, "server.py"), "3000"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir)

    print("\n[SUCCESS] Both servers launched! Press Ctrl+C to stop both.\n")

    # Give servers a moment to bind, then open browser
    time.sleep(1.5)
    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Servers stopped cleanly.")


if __name__ == "__main__":
    main()
