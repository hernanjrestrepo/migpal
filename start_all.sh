#!/bin/bash

# start_all.sh - Start MigPAL Backend and Frontend
# Usage: ./start_all.sh

set -e

echo "🚀 Starting MigPAL..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if backend virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}⚠️  Backend virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check if database exists
if [ ! -f "backend/migpal.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Initializing...${NC}"
    cd backend
    source .venv/bin/activate
    alembic upgrade head
    python populate_db.py
    cd ..
fi

# Start backend in background
echo -e "${GREEN}Starting backend...${NC}"
cd backend
source .venv/bin/activate
# Load .env file to override system environment variables
set -a
source .env
set +a
uvicorn main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s -f -o /dev/null http://localhost:8000/docs; then
    echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠️  Backend may still be starting...${NC}"
fi

# Start frontend in background
echo -e "${GREEN}Starting frontend...${NC}"
cd frontend
python3 server.py > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 2

# Check if frontend is running
if curl -s -f -o /dev/null http://localhost:3000; then
    echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend may still be starting...${NC}"
fi

echo ""
echo "=================================="
echo -e "${GREEN}✅ MigPAL is running!${NC}"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Login credentials:"
echo "  Email: admin@migpal.com"
echo "  Password: admin123"
echo ""
echo "Process IDs:"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or run: ./stop_all.sh"
echo ""
echo "Logs:"
echo "  Backend: logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo "=================================="
