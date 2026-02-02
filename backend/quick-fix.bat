@echo off
REM Quick fix for "service api is not running"

cd /d %~dp0

echo Stopping containers...
docker-compose down

echo Starting in correct order...
docker-compose up -d db redis
timeout /t 10 /nobreak > nul

docker-compose up -d api
timeout /t 10 /nobreak > nul

echo Status:
docker-compose ps

echo.
echo If all services are running, run:
echo   docker-compose exec api python scripts/init_db.py
