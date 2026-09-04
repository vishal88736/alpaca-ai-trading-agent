#!/usr/bin/env python3
"""
Single-entrypoint launcher.

Sets up `sys.path` so the `model` package (repo root) and `backend/app` package
are importable regardless of the working directory, then starts the FastAPI app.

Usage:
    python run.py                 # backend on http://localhost:8000
    python run.py --port 9000     # custom port
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Trading Agent backend")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()