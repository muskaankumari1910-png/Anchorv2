#!/bin/bash
# Anchor Deployment Script for Linux/Mac

set -e

echo "========================================"
echo "  Anchor Deployment Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker Compose is not available"
    echo "Please ensure Docker is running"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker is installed"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}[ACTION REQUIRED]${NC} Please edit .env file and add your GROQ_API_KEY"
    echo "Press any key after you've updated the .env file..."
    read -n 1 -s
fi

echo -e "${GREEN}[INFO]${NC} Checking for existing containers..."
docker compose ps

echo ""
echo "========================================"
echo "  Starting Deployment"
echo "========================================"
echo ""

# Stop existing containers
echo -e "${GREEN}[1/5]${NC} Stopping existing containers..."
docker compose down

# Build images
echo ""
echo -e "${GREEN}[2/5]${NC} Building Docker images..."
docker compose build

# Start services
echo ""
echo -e "${GREEN}[3/5]${NC} Starting services..."
docker compose up -d

# Wait for services to be ready
echo ""
echo -e "${GREEN}[4/5]${NC} Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo -e "${GREEN}[5/5]${NC} Checking service health..."
docker compose ps

echo ""
echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo ""
echo "Services running:"
echo "  - Frontend:  http://localhost"
echo "  - Backend:   http://localhost:8000"
echo "  - Database:  localhost:5432"
echo ""

# Test API connection
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} Backend API is responding"
else
    echo -e "${YELLOW}[WARNING]${NC} Backend API not responding yet"
    echo "It may still be starting up. Check logs with: docker compose logs -f"
fi

echo ""
echo "View logs: docker compose logs -f"
echo "Stop services: docker compose down"
echo ""
