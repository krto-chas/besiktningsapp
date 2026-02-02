"""Integration tests for inspection API."""
def test_create_inspection(client, auth_headers, sample_property):
    response = client.post('/api/v1/inspections', headers=auth_headers, json={
        'property_id': sample_property.id,
        'date': '2026-01-29',
        'status': 'draft'
    })
    assert response.status_code == 201
