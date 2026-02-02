"""Integration tests for property API."""
def test_create_property(client, auth_headers):
    response = client.post('/api/v1/properties', headers=auth_headers, json={
        'property_type': 'villa',
        'designation': 'TEST 1:1',
        'address': 'Test St'
    })
    assert response.status_code == 201
