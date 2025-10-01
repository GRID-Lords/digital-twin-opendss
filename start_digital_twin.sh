#!/bin/bash

# Digital Twin System Startup Script for SIH India Hackathon
# AI/ML enabled Digital Twin for EHV 400/220 kV Substation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🇮🇳 Starting Indian EHV Substation Digital Twin System"
echo "======================================================="

# Step 1: Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Step 2: Install/update dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q fastapi uvicorn websockets pandas numpy scikit-learn matplotlib pymodbus httpx python-multipart aiofiles py-dss-interface 2>/dev/null || true

# Step 3: Kill existing processes on ports
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 2

# Step 4: Start Backend Server
echo -e "${GREEN}Starting Backend Server...${NC}"
cd src
python backend_server.py &
BACKEND_PID=$!
cd ..
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server started successfully${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    echo "Check logs for errors"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Step 5: Check if frontend exists and install dependencies
if [ -d "frontend" ]; then
    echo -e "${GREEN}Starting Frontend...${NC}"
    cd frontend

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # Start frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo "Frontend PID: $FRONTEND_PID"
else
    echo -e "${YELLOW}Frontend directory not found. Running in backend-only mode.${NC}"
    FRONTEND_PID=""
fi

# Step 6: Display status
sleep 5
echo ""
echo "================================================"
echo -e "${GREEN}🎉 Digital Twin System Started Successfully!${NC}"
echo "================================================"
echo ""
echo "📍 Access Points:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • API Endpoints: http://localhost:8000"
echo "  • WebSocket: ws://localhost:8000/ws"
if [ -n "$FRONTEND_PID" ]; then
    echo "  • Frontend Dashboard: http://localhost:3000"
fi
echo ""
echo "🔧 Key Features:"
echo "  • Real-time SCADA monitoring"
echo "  • OpenDSS load flow simulation"
echo "  • AI/ML anomaly detection & failure prediction"
echo "  • Asset health monitoring"
echo "  • N-1 contingency analysis"
echo "  • Professional circuit visualization"
echo ""
echo "📊 API Endpoints:"
echo "  • GET  /api/assets         - View all assets"
echo "  • GET  /api/metrics        - Real-time metrics"
echo "  • GET  /api/scada/data     - SCADA data"
echo "  • POST /api/simulation     - Run simulations"
echo "  • GET  /api/ai/analysis    - AI/ML analysis"
echo "  • POST /api/control        - Send control commands"
echo ""
echo "🛑 To stop: Press Ctrl+C or run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Handle cleanup
cleanup() {
    echo ""
    echo "Shutting down Digital Twin System..."
    kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    deactivate 2>/dev/null || true
    echo "System stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
wait $BACKEND_PID