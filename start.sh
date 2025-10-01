#!/bin/bash

# Digital Twin System - Unified Startup Script
# Single point of entry for the entire system
# Supports both Docker and Local deployment modes

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo "==========================================================="
echo "   Indian EHV 400/220 kV Substation Digital Twin"
echo "   SIH India Hackathon - AI/ML Enabled System"
echo "==========================================================="
echo ""

# Deployment mode: docker, local, or auto (default)
MODE="${1:-auto}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
check_port() {
    if lsof -ti:$1 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port $1 is in use. Killing existing process...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Load environment configuration
load_env() {
    if [ -f .env ]; then
        echo -e "${BLUE}Loading environment configuration...${NC}"
        set -a
        source .env
        set +a
        echo -e "${GREEN}✓ Environment loaded${NC}"
    fi
}

# Function to start with Docker
start_docker() {
    echo -e "${BLUE}Starting with Docker Compose...${NC}"

    # Check Docker installation
    if ! command_exists docker; then
        echo -e "${RED}Docker is not installed. Install from: https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi

    if ! command_exists docker-compose; then
        echo -e "${RED}Docker Compose is not installed. Install from: https://docs.docker.com/compose/install/${NC}"
        exit 1
    fi

    # Load environment
    load_env

    # Build and start services
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose build

    echo -e "${BLUE}Starting Docker services...${NC}"
    docker-compose up -d

    echo -e "${GREEN}✓ Docker services started!${NC}"
    docker-compose ps
}

# Function to start locally
start_local() {
    # Load environment
    load_env

    # Step 1: Check Python environment
    echo -e "${BLUE}[1/5] Checking Python environment...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
    fi

    # Step 2: Install dependencies
    echo -e "${BLUE}[2/5] Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q fastapi uvicorn websockets pandas numpy scikit-learn matplotlib \
        httpx python-multipart aiofiles py-dss-interface pymodbus python-dotenv redis 2>/dev/null || true
    echo -e "${GREEN}✓ Dependencies installed${NC}"

    # Step 3: Clean up existing processes
    echo -e "${BLUE}[3/5] Preparing system...${NC}"
    check_port 8000
    check_port 3000
    echo -e "${GREEN}✓ System ready${NC}"

    # Step 4: Start backend
    echo -e "${BLUE}[4/5] Starting backend server...${NC}"
    python src/backend_server.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

    # Wait for backend
    sleep 5

    # Check if backend is running
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "${RED}✗ Backend failed to start. Check logs/backend.log${NC}"
        exit 1
    fi

    # Step 5: Start frontend (if exists)
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        echo -e "${BLUE}[5/5] Starting frontend...${NC}"
        cd frontend
        if [ ! -d "node_modules" ]; then
            npm install --silent
        fi
        DANGEROUSLY_DISABLE_HOST_CHECK=true npm start > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}Frontend not configured, running backend only${NC}"
    fi
}

# Create logs directory if not exists
mkdir -p logs

# Main execution based on mode
case "$MODE" in
    docker)
        start_docker
        ;;
    local)
        start_local
        ;;
    auto|*)
        # Auto-detect mode
        if command_exists docker && command_exists docker-compose && [ -f "docker-compose.yml" ]; then
            echo -e "${BLUE}Docker detected. Choose deployment mode:${NC}"
            echo "  1) Docker (recommended for production)"
            echo "  2) Local (for development)"
            echo ""
            read -p "Enter choice [1-2] (default: 2): " choice
            case $choice in
                1) start_docker ;;
                *) start_local ;;
            esac
        else
            start_local
        fi
        ;;
esac

# Display success message
display_success() {
    echo ""
    echo "==========================================================="
    echo -e "${GREEN} Digital Twin System Successfully Started!${NC}"
    echo "==========================================================="
    echo ""

    if [ "$MODE" = "docker" ]; then
        echo "Access Points:"
        echo "  • Frontend:    http://localhost:3000"
        echo "  • Backend API: http://localhost:8000"
        echo "  • API Docs:    http://localhost:8000/docs"
        echo "  • Grafana:     http://localhost:3001 (admin/admin)"
        echo "  • InfluxDB:    http://localhost:8086"
        echo ""
        echo "To stop: docker-compose down"
    else
        echo "Access Points:"
        echo "  • API Documentation: http://localhost:8000/docs"
        echo "  • Backend API: http://localhost:8000"
        echo "  • Health Check: http://localhost:8000/health"
        echo "  • Cache Stats: http://localhost:8000/api/cache/stats"
        [ ! -z "$FRONTEND_PID" ] && echo "  • Frontend Dashboard: http://localhost:3000"
        echo ""
        echo "Storage Strategy:"
        echo "  • Real-time data: Cached for ${REALTIME_CACHE_TTL:-60} seconds"
        echo "  • Metrics storage: Every ${METRICS_STORAGE_INTERVAL:-3600} seconds (hourly)"
        echo "  • Database: ${DB_TYPE:-sqlite}"
        echo ""
        echo "Key Features:"
        echo "  ✓ Complete asset modeling (Transformers, Breakers, CTs, CVTs)"
        echo "  ✓ SCADA/IoT data integration (Modbus, IEC 61850)"
        echo "  ✓ Advanced power flow simulation"
        echo "  ✓ Fault analysis & contingency studies"
        echo "  ✓ AI/ML anomaly detection & predictive maintenance"
        echo "  ✓ Real-time monitoring with WebSockets"
        echo "  ✓ Optimized data storage (hourly aggregation)"
        echo ""
        echo "API Endpoints:"
        echo "  GET  /api/assets                  - Asset management"
        echo "  GET  /api/metrics                 - Real-time metrics"
        echo "  GET  /api/metrics/historical     - Historical data"
        echo "  GET  /api/cache/stats            - Cache statistics"
        echo "  GET  /api/scada/data             - SCADA data"
        echo "  POST /api/simulation             - Run simulations"
        echo "  GET  /api/ai/analysis            - AI/ML analysis"
        echo "  WS   /ws                         - WebSocket"
        echo ""
        echo "To stop: Press Ctrl+C"
    fi
}

# Display success message after starting
display_success

# Cleanup on exit (for local mode)
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down Digital Twin...${NC}"
    if [ "$MODE" = "docker" ]; then
        docker-compose down
    else
        kill $BACKEND_PID 2>/dev/null || true
        [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
        deactivate 2>/dev/null || true
    fi
    echo -e "${GREEN}System stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running (for local mode)
if [ "$MODE" != "docker" ]; then
    wait $BACKEND_PID
fi