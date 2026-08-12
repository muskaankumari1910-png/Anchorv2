@echo off
REM Anchor Deployment Verification Script

echo ========================================
echo   Anchor Deployment Verification
echo ========================================
echo.

REM Check Docker
echo [1/8] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker is installed
) else (
    echo [FAIL] Docker is not installed
    echo Install from: https://www.docker.com/products/docker-desktop
    goto :end
)

REM Check Docker Compose
echo [2/8] Checking Docker Compose...
docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker Compose is available
) else (
    echo [FAIL] Docker Compose not available
    goto :end
)

REM Check if Docker is running
echo [3/8] Checking if Docker is running...
docker ps >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker is running
) else (
    echo [FAIL] Docker is not running. Please start Docker Desktop
    goto :end
)

REM Check .env file
echo [4/8] Checking .env file...
if exist ".env" (
    echo [OK] .env file exists
    findstr "GROQ_API_KEY" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] GROQ_API_KEY is configured
    ) else (
        echo [WARNING] GROQ_API_KEY not found in .env
    )
) else (
    echo [WARNING] .env file not found
    echo Creating from .env.example...
    copy .env.example .env >nul 2>&1
)

REM Check required files
echo [5/8] Checking required files...
if exist "docker-compose.yml" (
    echo [OK] docker-compose.yml found
) else (
    echo [FAIL] docker-compose.yml not found
    goto :end
)

if exist "backend\Dockerfile" (
    echo [OK] backend/Dockerfile found
) else (
    echo [FAIL] backend/Dockerfile not found
    goto :end
)

if exist "frontend\Dockerfile" (
    echo [OK] frontend/Dockerfile found
) else (
    echo [FAIL] frontend/Dockerfile not found
    goto :end
)

REM Check if services are running
echo [6/8] Checking if services are running...
docker compose ps 2>nul | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Services are running
    docker compose ps
) else (
    echo [INFO] Services are not running yet
    echo Run deploy.bat to start services
)

REM Check disk space
echo [7/8] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c ^| findstr /C:"bytes free"') do set FREE=%%a
echo [INFO] Free disk space: %FREE% bytes

REM Check ports
echo [8/8] Checking port availability...
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 80 is in use
    echo You may need to stop other services or change ports
) else (
    echo [OK] Port 80 is available
)

netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 is in use
) else (
    echo [OK] Port 8000 is available
)

netstat -ano | findstr ":5432 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 5432 is in use
) else (
    echo [OK] Port 5432 is available
)

echo.
echo ========================================
echo   Verification Complete
echo ========================================
echo.

REM Final recommendation
docker compose ps 2>nul | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Anchor is deployed and running!
    echo.
    echo Access the application:
    echo   Frontend: http://localhost
    echo   Backend:  http://localhost:8000
    echo   API Docs: http://localhost:8000/docs
    echo.
    echo View logs: docker compose logs -f
) else (
    echo [READY] System is ready for deployment
    echo.
    echo To deploy, run:
    echo   deploy.bat
    echo.
)

:end
echo.
pause
