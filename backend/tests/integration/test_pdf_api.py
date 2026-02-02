"""Integration tests for PDF API."""
def test_generate_pdf(client, auth_headers, sample_inspection):
    response = client.post('/api/v1/pdf/generate', headers=auth_headers, json={
        'inspection_id': sample_inspection.id,
        'status': 'draft'
    })
    assert response.status_code == 201
