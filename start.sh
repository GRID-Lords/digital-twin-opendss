#!/bin/bash

# Indian EHV Substation Digital Twin - Complete System Startup Script
# This script starts both backend and frontend with proper logging and verification

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Create logs directory
mkdir -p logs

# Log file
LOG_FILE="logs/startup.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "🇮🇳 Indian EHV Substation Digital Twin - System Startup"
echo "======================================================"
echo "Timestamp: $(date)"
echo "Log file: $LOG_FILE"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -ti:$1 >/dev/null 2>&1
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    if port_in_use $port; then
        log_warning "Port $port is in use. Killing existing processes..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Step 1: System Requirements Check
log_step "Checking system requirements..."

# Check Python
if ! command_exists python3; then
    log_error "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    log_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi
log_success "Python $PYTHON_VERSION detected"

# Check Node.js
if ! command_exists node; then
    log_error "Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    log_error "Node.js 16+ is required. Current version: $(node -v)"
    exit 1
fi
log_success "Node.js $(node -v) detected"

# Check npm
if ! command_exists npm; then
    log_error "npm is not installed"
    exit 1
fi
log_success "npm $(npm -v) detected"

# Step 2: Clean up existing processes
log_step "Cleaning up existing processes..."
kill_port 3000
kill_port 8000
log_success "Ports cleared"

# Step 3: Install Python Dependencies
log_step "Installing Python dependencies..."
python3 -m pip install --user --quiet \
    fastapi uvicorn websockets pandas numpy scikit-learn \
    matplotlib opendssdirect pymodbus requests sqlite3 \
    pytest pytest-asyncio httpx
log_success "Python dependencies installed"

# Step 4: Install Frontend Dependencies
log_step "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
    log_success "Frontend dependencies installed"
else
    log_success "Frontend dependencies already installed"
fi
cd ..

# Step 5: Run Tests
log_step "Running system tests..."

# Run Python tests
log_info "Running backend tests..."
python3 -m pytest tests/ -v --tb=short || {
    log_warning "Some tests failed, but continuing..."
}

# Run frontend tests
log_info "Running frontend tests..."
cd frontend
npm test -- --watchAll=false --passWithNoTests || {
    log_warning "Some frontend tests failed, but continuing..."
}
cd ..

# Step 6: Train AI/ML Models
log_step "Training AI/ML models..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from models.ai_ml_models import SubstationAIManager
import logging

logging.basicConfig(level=logging.INFO)
ai_manager = SubstationAIManager()
ai_manager.initialize_with_synthetic_data()
print('AI/ML models trained successfully')
"
log_success "AI/ML models trained and ready"

# Step 7: Start Backend
log_step "Starting backend server..."
python3 main.py &
BACKEND_PID=$!
log_info "Backend PID: $BACKEND_PID"

# Wait for backend to start
log_info "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/metrics >/dev/null 2>&1; then
        log_success "Backend server started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Backend failed to start within 30 seconds"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Step 8: Start Frontend
log_step "Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
log_info "Frontend PID: $FRONTEND_PID"
cd ..

# Wait for frontend to start
log_info "Waiting for frontend to start..."
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        log_success "Frontend server started successfully"
        break
    fi
    if [ $i -eq 60 ]; then
        log_error "Frontend failed to start within 60 seconds"
        kill $FRONTEND_PID 2>/dev/null || true
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Step 9: System Verification
log_step "Verifying system functionality..."

# Test API endpoints
log_info "Testing API endpoints..."
curl -s http://localhost:8000/api/assets >/dev/null && log_success "Assets API working"
curl -s http://localhost:8000/api/metrics >/dev/null && log_success "Metrics API working"
curl -s http://localhost:8000/api/scada/data >/dev/null && log_success "SCADA API working"
curl -s http://localhost:8000/api/ai/analysis >/dev/null && log_success "AI API working"

# Test WebSocket
log_info "Testing WebSocket connection..."
python3 -c "
import websocket
import time
import threading

def on_message(ws, message):
    print('WebSocket message received')
    ws.close()

def on_error(ws, error):
    print(f'WebSocket error: {error}')

def on_close(ws, close_status_code, close_msg):
    print('WebSocket closed')

def on_open(ws):
    print('WebSocket connected')
    time.sleep(1)
    ws.close()

ws = websocket.WebSocketApp('ws://localhost:8000/ws',
                          on_open=on_open,
                          on_message=on_message,
                          on_error=on_error,
                          on_close=on_close)
ws.run_forever()
" && log_success "WebSocket connection working"

# Step 10: Final Status
echo ""
echo "🎉 Digital Twin System Started Successfully!"
echo "============================================="
echo ""
echo "🌐 Access Points:"
echo "  • Frontend Dashboard: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • WebSocket: ws://localhost:8000/ws"
echo ""
echo "📊 System Status:"
echo "  • Backend PID: $BACKEND_PID"
echo "  • Frontend PID: $FRONTEND_PID"
echo "  • Log file: $LOG_FILE"
echo ""
echo "🔧 Features Available:"
echo "  • Real-time monitoring dashboard"
echo "  • Asset management and control"
echo "  • SCADA data visualization"
echo "  • AI/ML analytics and predictions"
echo "  • Professional circuit visualizations"
echo ""
echo "🛑 To stop the system:"
echo "  • Press Ctrl+C"
echo "  • Or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Keep the script running and handle cleanup
cleanup() {
    log_info "Shutting down system..."
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    log_success "System shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID