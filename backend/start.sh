#!/bin/bash
# MigPAL Backend Start Script

cd "$(dirname "$0")"

echo "🚀 Starting MigPAL Backend..."

# Activate virtual environment
source .venv/bin/activate

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
