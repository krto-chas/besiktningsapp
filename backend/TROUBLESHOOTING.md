# TROUBLESHOOTING GUIDE

## Problem: "service api is not running"

### Lösning 1: Starta services i rätt ordning

```bash
cd /mnt/user-data/outputs/backend

# 1. Stäng ner allt
docker-compose down

# 2. Starta databas först
docker-compose up -d db redis

# 3. Vänta på att db är redo (viktigt!)
docker-compose exec db pg_isready -U postgres

# 4. Starta API
docker-compose up -d api

# 5. Kolla status
docker-compose ps
docker-compose logs api
```

### Lösning 2: Kolla loggar för fel

```bash
# Se vad som gick fel
docker-compose logs api

# Följ loggar live
docker-compose logs -f api
```

### Lösning 3: Bygg om container

```bash
# Om det är import errors eller liknande
docker-compose build --no-cache api
docker-compose up -d
```

### Lösning 4: Fixa "version is obsolete" varning

Redigera `docker-compose.yml` och ta bort första raden:
```yaml
version: '3.8'  # <-- TA BORT DENNA RAD
```

### Vanliga fel och lösningar:

#### Fel: Port 5000 redan används
```bash
# Ändra port i docker-compose.yml
services:
  api:
    ports:
      - "5001:5000"  # Använd 5001 istället
```

#### Fel: Database connection refused
```bash
# Vänta på att PostgreSQL startar
sleep 10
docker-compose exec db pg_isready -U postgres
```

#### Fel: No module named 'app'
```bash
# Rebuild med pip install
docker-compose build --no-cache api
docker-compose up -d api
```

## Komplett setup från scratch:

```bash
# 1. Rensa allt
docker-compose down -v

# 2. Fixa docker-compose.yml (ta bort version: '3.8')

# 3. Starta bara databas
docker-compose up -d db redis

# 4. Vänta 5-10 sekunder
sleep 10

# 5. Verifiera db
docker-compose exec db pg_isready -U postgres

# 6. Starta API
docker-compose up -d api

# 7. Vänta på att API startar
sleep 5

# 8. Kolla att allt är igång
docker-compose ps

# 9. Nu initiera databas
docker-compose exec api python scripts/init_db.py
docker-compose exec api python scripts/seed_data.py

# 10. Testa!
curl http://localhost:5000/health
```

## Quick fix script:

```bash
#!/bin/bash
echo "=== Startar backend från scratch ==="

cd /mnt/user-data/outputs/backend

echo "1. Stoppar allt..."
docker-compose down -v

echo "2. Startar databas..."
docker-compose up -d db redis

echo "3. Väntar på PostgreSQL..."
sleep 10

echo "4. Startar API..."
docker-compose up -d api

echo "5. Väntar på API..."
sleep 10

echo "6. Kollar status..."
docker-compose ps

echo "7. Initierar databas..."
docker-compose exec api python scripts/init_db.py
docker-compose exec api python scripts/seed_data.py

echo "8. Testar health check..."
curl http://localhost:5000/health

echo ""
echo "✅ Klart!"
```

Spara som `restart.sh` och kör: `bash restart.sh`
