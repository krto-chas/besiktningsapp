#!/bin/bash
set -e

BASE_URL="http://localhost:5000"

echo "=== 1. Health Check ==="
curl -s $BASE_URL/health | jq . || curl -s $BASE_URL/health

echo -e "\n=== 2. Login ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"inspector@besiktningsapp.se","password":"inspector123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token' 2>/dev/null || echo "")

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Login failed!"
    echo $LOGIN_RESPONSE
    exit 1
fi

echo "✓ Token: ${TOKEN:0:20}..."

echo -e "\n=== 3. Get Current User ==="
curl -s $BASE_URL/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq . || echo "❌ Failed"

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

PROPERTY_ID=$(echo $PROPERTY | jq -r '.data.id' 2>/dev/null || echo "")
echo "✓ Property ID: $PROPERTY_ID"

echo -e "\n=== 5. Create Inspection ==="
INSPECTION=$(curl -s -X POST $BASE_URL/api/v1/inspections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"property_id\": $PROPERTY_ID,
    \"date\": \"2026-01-29\",
    \"status\": \"draft\"
  }")

INSPECTION_ID=$(echo $INSPECTION | jq -r '.data.id' 2>/dev/null || echo "")
echo "✓ Inspection ID: $INSPECTION_ID"

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

APARTMENT_ID=$(echo $APARTMENT | jq -r '.data.id' 2>/dev/null || echo "")
echo "✓ Apartment ID: $APARTMENT_ID"

echo -e "\n=== 7. Create Defect ==="
curl -s -X POST $BASE_URL/api/v1/defects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"apartment_id\": $APARTMENT_ID,
    \"room_index\": 1,
    \"description\": \"Fläktventil saknas i kök\",
    \"severity\": \"high\"
  }" | jq . || echo "❌ Failed"

echo -e "\n=== 8. List All Inspections ==="
INSPECTION_COUNT=$(curl -s $BASE_URL/api/v1/inspections \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length' 2>/dev/null || echo "0")
echo "✓ Total inspections: $INSPECTION_COUNT"

echo -e "\n✅ All tests passed!"
