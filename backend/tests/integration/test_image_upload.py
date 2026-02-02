"""Integration tests for image upload."""
import io
def test_upload_image(client, auth_headers):
    data = {'file': (io.BytesIO(b'test'), 'test.jpg')}
    response = client.post('/api/v1/uploads/images', headers=auth_headers, data=data)
    assert response.status_code in [200, 201]
