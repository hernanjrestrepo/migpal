#!/bin/bash

# stop_all.sh - Stop MigPAL Backend and Frontend

echo "🛑 Stopping MigPAL..."

# Kill backend (uvicorn)
pkill -f "uvicorn app.api:app" && echo "✓ Backend stopped" || echo "⚠️  Backend not running"

# Kill frontend (python server)
pkill -f "python3 server.py" && echo "✓ Frontend stopped" || echo "⚠️  Frontend not running"

echo ""
echo "✅ MigPAL stopped"
