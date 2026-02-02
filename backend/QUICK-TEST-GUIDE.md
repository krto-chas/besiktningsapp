# QUICK TEST GUIDE - Besiktningsapp Backend

## 🚀 Snabbstart (5 minuter)

### 1. Starta Backend
```bash
cd /mnt/user-data/outputs/backend

# Starta alla services (PostgreSQL, Redis, Flask)
docker-compose up -d

# Kolla att allt är igång
docker-compose ps
```

### 2. Initiera Databasen
```bash
# Skapa tabeller
docker-compose exec api python scripts/init_db.py

# Seed testdata (admin + inspector användare)
docker-compose exec api python scripts/seed_data.py
```

### 3. Testa API:et

#### Health Check
```bash
curl http://localhost:5000/health
# Förväntat svar: {"status": "healthy", ...}
```

#### Login som Inspector
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "inspector@besiktningsapp.se",
    "password": "inspector123"
  }'

# Spara access_token från svaret!
```

#### Skapa en Fastighet
```bash
TOKEN="<din_access_token>"

curl -X POST http://localhost:5000/api/v1/properties \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_type": "flerbostadshus",
    "designation": "STOCKHOLM 1:1",
    "address": "Storgatan 1",
    "postal_code": "11122",
    "city": "Stockholm",
    "num_apartments": 24
  }'
```

#### Hämta alla Fastigheter
```bash
curl http://localhost:5000/api/v1/properties \
  -H "Authorization: Bearer $TOKEN"
```

#### Skapa en Besiktning
```bash
curl -X POST http://localhost:5000/api/v1/inspections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "date": "2026-01-29",
    "status": "draft"
  }'
```

---

## 🧪 Kör Tests

```bash
# Alla tester
docker-compose exec api pytest

# Med output
docker-compose exec api pytest -v

# Med coverage
docker-compose exec api pytest --cov=app --cov-report=term-missing

# Specifika tester
docker-compose exec api pytest tests/unit/
docker-compose exec api pytest tests/integration/
docker-compose exec api pytest tests/e2e/
```

---

## 🔍 Debug & Logs

```bash
# Se loggar
docker-compose logs -f api

# Gå in i containern
docker-compose exec api bash

# Kolla databas
docker-compose exec db psql -U postgres -d besiktningsapp
```

---

## 📊 Fullständigt Test-Scenario

### Skript: `test_full_flow.sh`
```bash
#!/bin/bash
set -e

BASE_URL="http://localhost:5000"

echo "=== 1. Health Check ==="
curl -s $BASE_URL/health | jq .

echo -e "\n=== 2. Login ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"inspector@besiktningsapp.se","password":"inspector123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
echo "Token: ${TOKEN:0:20}..."

echo -e "\n=== 3. Get Current User ==="
curl -s $BASE_URL/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n=== 4. Create Property ==="
PROPERTY=$(curl -s -X POST $BASE_URL/api/v1/properties \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_type": "flerbostadshus",
    "designation": "TEST 1:1",
    "address": "Testgatan 1",
    "city": "Stockholm",
    "num_apartments": 12
  }')

PROPERTY_ID=$(echo $PROPERTY | jq -r '.data.id')
echo "Property ID: $PROPERTY_ID"

echo -e "\n=== 5. Create Inspection ==="
INSPECTION=$(curl -s -X POST $BASE_URL/api/v1/inspections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"property_id\": $PROPERTY_ID,
    \"date\": \"2026-01-29\",
    \"status\": \"draft\"
  }")

INSPECTION_ID=$(echo $INSPECTION | jq -r '.data.id')
echo "Inspection ID: $INSPECTION_ID"

echo -e "\n=== 6. Create Apartment ==="
APARTMENT=$(curl -s -X POST $BASE_URL/api/v1/apartments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"inspection_id\": $INSPECTION_ID,
    \"apartment_number\": \"1201\",
    \"rooms\": [
      {\"index\": 0, \"type\": \"hall\"},
      {\"index\": 1, \"type\": \"kok\"},
      {\"index\": 2, \"type\": \"sovrum\"}
    ]
  }")

APARTMENT_ID=$(echo $APARTMENT | jq -r '.data.id')
echo "Apartment ID: $APARTMENT_ID"

echo -e "\n=== 7. Create Defect ==="
curl -s -X POST $BASE_URL/api/v1/defects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"apartment_id\": $APARTMENT_ID,
    \"room_index\": 1,
    \"description\": \"Fläktventil saknas i kök\",
    \"severity\": \"high\"
  }" | jq .

echo -e "\n=== 8. List All Inspections ==="
curl -s $BASE_URL/api/v1/inspections \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length'

echo -e "\n✅ All tests passed!"
```

Spara som `test_full_flow.sh` och kör:
```bash
chmod +x test_full_flow.sh
./test_full_flow.sh
```

---

## 🎯 Testanvändare

### Inspector (Normal användare)
- **Email**: inspector@besiktningsapp.se
- **Password**: inspector123
- **Role**: inspector

### Admin
- **Email**: admin@besiktningsapp.se
- **Password**: admin123
- **Role**: admin

---

## 📱 API Endpoints att Testa

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Current user
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Properties
- `GET /api/v1/properties` - List all
- `POST /api/v1/properties` - Create
- `GET /api/v1/properties/{id}` - Get one
- `PATCH /api/v1/properties/{id}` - Update
- `DELETE /api/v1/properties/{id}` - Delete

### Inspections
- `GET /api/v1/inspections` - List all
- `POST /api/v1/inspections` - Create
- `GET /api/v1/inspections/{id}` - Get one
- `PATCH /api/v1/inspections/{id}` - Update
- `DELETE /api/v1/inspections/{id}` - Delete

### Apartments
- `GET /api/v1/apartments` - List all
- `POST /api/v1/apartments` - Create
- `GET /api/v1/apartments/{id}` - Get one
- `PATCH /api/v1/apartments/{id}` - Update
- `DELETE /api/v1/apartments/{id}` - Delete

### Defects
- `GET /api/v1/defects` - List all
- `POST /api/v1/defects` - Create
- `GET /api/v1/defects/{id}` - Get one
- `PATCH /api/v1/defects/{id}` - Update
- `DELETE /api/v1/defects/{id}` - Delete

### Measurements
- `GET /api/v1/measurements` - List all
- `POST /api/v1/measurements` - Create
- `GET /api/v1/measurements/{id}` - Get one
- `PATCH /api/v1/measurements/{id}` - Update
- `DELETE /api/v1/measurements/{id}` - Delete

### Sync
- `GET /api/v1/sync/handshake` - Sync handshake
- `POST /api/v1/sync/push` - Push changes
- `GET /api/v1/sync/pull` - Pull changes

### PDF
- `POST /api/v1/pdf/generate` - Generate PDF

### Uploads
- `POST /api/v1/uploads/images` - Upload image
- `POST /api/v1/uploads/presigned-url` - Get presigned URL

### Health
- `GET /health` - Health check
- `GET /ready` - Readiness check

---

## 🐛 Felsökning

### Containrar startar inte
```bash
docker-compose down
docker-compose up -d
docker-compose logs
```

### Databas connection error
```bash
# Vänta tills PostgreSQL är redo
docker-compose exec db pg_isready

# Kontrollera credentials
docker-compose exec db psql -U postgres -l
```

### Import errors
```bash
# Rebuild container
docker-compose build api
docker-compose up -d api
```

### Port redan används
```bash
# Ändra port i docker-compose.yml
ports:
  - "5001:5000"  # Använd 5001 istället
```

---

## 🎉 Klart!

Nu kan du testa hela backend-API:et! 

**Nästa steg:**
1. Testa med Postman (importera endpoints)
2. Bygg React Native appen
3. Implementera offline sync
4. Deploy till produktion

EOF

cat QUICK-TEST-GUIDE.md
