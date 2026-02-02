"""Integration tests for auth API."""
def test_login_success(client, test_user):
    response = client.post('/api/v1/auth/login', json={'email': 'test@example.com', 'password': 'password123'})
    assert response.status_code == 200

def test_get_me(client, auth_headers):
    response = client.get('/api/v1/auth/me', headers=auth_headers)
    assert response.status_code == 200
