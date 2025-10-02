#!/bin/bash

# Frontend startup script for Indian EHV Substation Digital Twin

echo "🚀 Starting Frontend for Indian EHV Substation Digital Twin"
echo "=========================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/api/metrics > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend not detected on http://localhost:8000"
    echo "   Please start the backend first:"
    echo "   python3 main.py"
    echo ""
    echo "   Or run the full startup script:"
    echo "   python3 examples/start_digital_twin.py"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🌐 Starting React development server..."
echo "======================================"
echo "Frontend will be available at: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "WebSocket: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the React development server
npm start