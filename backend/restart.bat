@echo off
echo ====================================
echo BESIKTNINGSAPP - Backend Restart
echo ====================================
echo.

cd /d %~dp0

echo [1/8] Stopping all containers...
docker-compose down

echo.
echo [2/8] Starting database...
docker-compose up -d db redis

echo.
echo [3/8] Waiting for PostgreSQL (15 seconds)...
timeout /t 15 /nobreak > nul

echo.
echo [4/8] Verifying database...
docker-compose exec db pg_isready -U postgres

echo.
echo [5/8] Starting API...
docker-compose up -d api

echo.
echo [6/8] Waiting for API (15 seconds)...
timeout /t 15 /nobreak > nul

echo.
echo [7/8] Checking status...
docker-compose ps

echo.
echo [8/8] Checking logs...
docker-compose logs --tail=20 api

echo.
echo ====================================
echo Setup complete!
echo ====================================
echo.
echo Next steps:
echo   1. docker-compose exec api python scripts/init_db.py
echo   2. docker-compose exec api python scripts/seed_data.py
echo   3. curl http://localhost:5000/health
echo.
