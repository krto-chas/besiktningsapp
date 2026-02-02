"""E2E test for complete workflow."""
def test_complete_workflow(client, auth_headers):
    # Create property
    prop = client.post('/api/v1/properties', headers=auth_headers, json={
        'property_type': 'villa',
        'designation': 'E2E 1:1',
        'address': 'E2E St'
    })
    assert prop.status_code == 201
    
    # Create inspection
    insp = client.post('/api/v1/inspections', headers=auth_headers, json={
        'property_id': prop.json['data']['id'],
        'date': '2026-01-29',
        'status': 'draft'
    })
    assert insp.status_code == 201
