#!/usr/bin/env python
"""Simple run script for development"""

import subprocess
import sys

if __name__ == "__main__":
    # Run with uv
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "claude_ui.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])