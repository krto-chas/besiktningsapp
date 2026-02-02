# BESIKTNINGSAPP - GRUNDLÄGGANDE KONFIGURATIONSFILER

## 📋 Översikt

Dessa filer utgör grunden för besiktningsapplikationens backend och utvecklingsmiljö. Alla filer är skapade enligt 12-factor app-principen och stödjer både utveckling och produktion.

## 📁 Skapade filer

### Root-nivå

1. **`.env.example`**
   - Mall för miljövariabler
   - Täcker alla konfigurationsområden: databas, auth, storage, sync, etc.
   - Kopiera till `.env` och fyll i värden
   - **Användning**: `cp .env.example .env`

2. **`docker-compose.yml`**
   - Utvecklingsmiljö med Docker Compose
   - Services: PostgreSQL, Redis, MinIO, Backend API, Adminer
   - Hot-reload aktiverad för utveckling
   - Volumes för persistent data
   - **Användning**: `docker-compose up -d`

3. **`docker-compose.prod.yml`**
   - Produktionsmiljö (overlay over docker-compose.yml)
   - Optimerade inställningar för produktion
   - Gunicorn med flera workers
   - Nginx reverse proxy
   - Celery workers för async tasks
   - **Användning**: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

4. **`Makefile`**
   - Samling av vanliga kommandon
   - Täcker: setup, docker, database, testing, deployment, etc.
   - **Användning**: `make help` för att se alla kommandon

### Backend-mapp (`/backend`)

5. **`Dockerfile`**
   - Multi-stage Dockerfile med development och production targets
   - Base image: Python 3.11-slim
   - Skapar non-root user (appuser)
   - Health checks inkluderade
   - **Användning**: 
     - Dev: `docker build --target development -t besiktningsapp:dev .`
     - Prod: `docker build --target production -t besiktningsapp:prod .`

6. **`Dockerfile.prod`**
   - Optimerad produktions-Dockerfile
   - Virtual environment i builder stage
   - Minimal runtime image
   - Security hardening
   - **Användning**: `docker build -f Dockerfile.prod -t besiktningsapp:prod .`

7. **`requirements.txt`**
   - Alla produktionsberoenden
   - Pinnade versioner för reproducerbarhet
   - Inkluderar: Flask, SQLAlchemy, Pydantic, JWT, boto3, reportlab, etc.
   - **Användning**: `pip install -r requirements.txt`

8. **`requirements-dev.txt`**
   - Utvecklings- och testverktyg
   - Inkluderar: pytest, flake8, black, mypy, ipython, etc.
   - **Användning**: `pip install -r requirements-dev.txt`

9. **`setup.py`**
   - Package setup för backend
   - Metadata och entry points
   - Console scripts
   - **Användning**: `pip install -e .`

10. **`pytest.ini`**
    - Pytest-konfiguration
    - Test markers (unit, integration, e2e, etc.)
    - Coverage settings
    - Logging konfiguration
    - **Användning**: Automatiskt används av pytest

11. **`.flake8`**
    - Flake8 linting-konfiguration
    - Max line length: 100
    - Kompatibel med black
    - Per-file ignores
    - **Användning**: `flake8 app tests`

12. **`mypy.ini`**
    - MyPy statisk typkontroll
    - Strict mode aktiverad
    - Plugin för SQLAlchemy och Pydantic
    - Per-module settings
    - **Användning**: `mypy app`

## 🚀 Snabbstart

### 1. Initial setup

```bash
# Kopiera miljövariabler
cp .env.example .env

# Redigera .env med dina värden
nano .env

# Eller använd Makefile
make setup
```

### 2. Starta utvecklingsmiljön

```bash
# Med Makefile
make up

# Eller direkt med docker-compose
docker-compose up -d
```

### 3. Verifiera att allt fungerar

```bash
# Kolla status
make ps

# Visa loggar
make logs

# Testa health endpoints
make health
```

### 4. Initiera databasen

```bash
# Kör migrations och seed data
make db-init

# Eller manuellt
docker-compose exec backend flask db upgrade
docker-compose exec backend python scripts/seed_data.py
```

### 5. Öppna utvecklingsverktyg

- **Backend API**: http://localhost:5000
- **Adminer (DB UI)**: http://localhost:8080
- **MinIO Console**: http://localhost:9001

## 🧪 Testa installationen

```bash
# Kör alla tester
make test

# Kör backend-tester med coverage
make backend-test-cov

# Lint och format check
make lint

# Health check
curl http://localhost:5000/health
curl http://localhost:5000/ready
```

## 📦 Viktiga kommandon

### Docker

```bash
make up          # Starta alla services
make down        # Stoppa alla services
make restart     # Restart services
make logs        # Visa loggar
make build       # Bygg images
make clean       # Rensa allt
```

### Database

```bash
make db-migrate MSG="description"  # Skapa migration
make db-upgrade                    # Applicera migrations
make db-shell                      # Öppna psql shell
make db-backup                     # Backup databas
```

### Testing

```bash
make test              # Alla tester
make test-unit         # Unit tests
make test-integration  # Integration tests
make backend-test-cov  # Med coverage
```

### Code Quality

```bash
make lint         # Kör alla linters
make format       # Formatera kod
make security-check  # Security audit
```

## 🔐 Säkerhet

### Hemligheter

1. **ALDRIG** committa `.env` till version control
2. Generera starka secrets: `make generate-secret`
3. I produktion: använd secrets manager (Kubernetes secrets, AWS Secrets Manager, etc.)

### Produktionsmiljö

```bash
# Generera nya secrets för produktion
export SECRET_KEY=$(make generate-secret)
export JWT_SECRET_KEY=$(make generate-secret)
export POSTGRES_PASSWORD=$(make generate-secret)

# Starta prod environment
make prod-up
```

## 📊 Miljövariabler (viktiga)

### Minimum required

```env
SECRET_KEY=<strong-secret>
JWT_SECRET_KEY=<strong-secret>
DATABASE_URL=postgresql://user:pass@host:5432/db
STORAGE_BACKEND=local  # eller 's3'
```

### Storage

```env
# För lokal storage (dev)
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/storage

# För S3/MinIO (prod)
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY_ID=<key>
S3_SECRET_ACCESS_KEY=<secret>
S3_BUCKET_NAME=besiktningsapp
```

## 🏗️ Arkitektur

### Services i utvecklingsmiljö

1. **PostgreSQL** (port 5432) - Primär databas
2. **Redis** (port 6379) - Cache och rate limiting
3. **MinIO** (port 9000/9001) - S3-kompatibel object storage
4. **Backend API** (port 5000) - Flask API
5. **Adminer** (port 8080) - Database UI

### Volumes

- `postgres_data` - PostgreSQL data
- `redis_data` - Redis persistence
- `minio_data` - MinIO object storage
- `backend_storage` - Lokal fillagring
- `backend_logs` - Application logs

## 🔧 Troubleshooting

### Problem: Port redan använd

```bash
# Hitta process på port 5000
lsof -i :5000

# Eller ändra port i docker-compose.yml
ports:
  - "5001:5000"  # Extern:Intern
```

### Problem: Permission denied

```bash
# Sätt rätt permissions på volumes
sudo chown -R $USER:$USER backend/storage
```

### Problem: Database connection failed

```bash
# Vänta tills PostgreSQL är ready
docker-compose logs postgres

# Eller restart
make restart
```

### Problem: Migrations failed

```bash
# Återställ migrations
make db-downgrade
make db-upgrade

# Eller droppa och återskapa
make clean
make setup
```

## 📝 Nästa steg

Nu när grundläggande konfiguration är klar, fortsätt med:

1. **App-struktur**: Skapa `app/__init__.py`, `app/main.py`, etc.
2. **Models**: Implementera domänmodeller i `app/models/`
3. **Schemas**: Skapa Pydantic schemas i `app/schemas/`
4. **API endpoints**: Implementera routes i `app/api/v1/`
5. **Services**: Business logic i `app/services/`
6. **Tests**: Skriv tester i `tests/`

## 🤝 Development workflow

```bash
# 1. Skapa feature branch
git checkout -b feature/my-feature

# 2. Starta dev environment
make up

# 3. Utveckla och testa
make backend-test

# 4. Formatera och lint
make format
make lint

# 5. Commit
git add .
git commit -m "feat: my feature"

# 6. Push
git push origin feature/my-feature
```

## 📚 Referenser

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [12-Factor App](https://12factor.net/)
- [Pytest Documentation](https://docs.pytest.org/)

## ✅ Checkpoints

- [ ] `.env` file skapad och konfigurerad
- [ ] Docker containers startar utan fel
- [ ] Database migrations körs
- [ ] Health endpoints svarar (200 OK)
- [ ] Kan köra tester (`make test`)
- [ ] Kan komma åt Adminer och se databas
- [ ] Kan komma åt MinIO console

---

**Status**: ✅ Grundläggande konfiguration komplett  
**Nästa**: Implementera app-struktur och domänmodeller
