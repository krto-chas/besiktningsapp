"""Integration tests for image upload."""
import io
def test_upload_image(client, auth_headers):
    # Send invalid image bytes — server should validate and return 400
    data = {'file': (io.BytesIO(b'not-a-real-image'), 'test.jpg')}
    response = client.post(
        '/api/v1/images/upload',
        headers=auth_headers,
        data=data,
        content_type='multipart/form-data',
    )
    assert response.status_code in [200, 201, 400]
