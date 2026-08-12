@echo off
REM Anchor Deployment Script for Windows

echo ========================================
echo   Anchor Deployment Script
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not available
    echo Please ensure Docker Desktop is running
    pause
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env file and add your GROQ_API_KEY
    echo Press any key after you've updated the .env file...
    pause >nul
)

echo [INFO] Checking for existing containers...
docker compose ps

echo.
echo ========================================
echo   Starting Deployment
echo ========================================
echo.

REM Stop existing containers
echo [1/5] Stopping existing containers...
docker compose down

REM Build images
echo.
echo [2/5] Building Docker images...
docker compose build

REM Start services
echo.
echo [3/5] Starting services...
docker compose up -d

REM Wait for services to be ready
echo.
echo [4/5] Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check service health
echo.
echo [5/5] Checking service health...
docker compose ps

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo Services running:
echo   - Frontend:  http://localhost
echo   - Backend:   http://localhost:8000
echo   - Database:  localhost:5432
echo.
echo Testing API connection...
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend API is responding
) else (
    echo [WARNING] Backend API not responding yet
    echo It may still be starting up. Check logs with: docker compose logs -f
)

echo.
echo View logs: docker compose logs -f
echo Stop services: docker compose down
echo.
pause
