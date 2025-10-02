#!/bin/bash

# Digital Twin Docker Compose Startup Script

echo "======================================"
echo "Digital Twin System - Docker Deployment"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment configuration..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using default configuration."
fi

# Build and start services
echo "Starting Digital Twin services..."

# Start only the databases first
echo "Starting database services..."
docker-compose up -d timescaledb redis influxdb

# Wait for databases to be ready
echo "Waiting for databases to initialize..."
sleep 10

# Start remaining services
echo "Starting application services..."
docker-compose up -d

# Show running containers
echo ""
echo "Running containers:"
docker-compose ps

echo ""
echo "======================================"
echo "Digital Twin System is starting up!"
echo "======================================"
echo ""
echo "Access points:"
echo "  - Frontend:    http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs:    http://localhost:8000/docs"
echo "  - Grafana:     http://localhost:3001 (admin/admin)"
echo "  - InfluxDB:    http://localhost:8086"
echo ""
echo "Health check:"
echo "  curl http://localhost:8000/health"
echo ""
echo "View logs:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "Stop all services:"
echo "  docker-compose down"
echo ""