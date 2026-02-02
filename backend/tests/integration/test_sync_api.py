"""Integration tests for sync API."""
def test_sync_handshake(client, auth_headers):
    response = client.get('/api/v1/sync/handshake', headers=auth_headers)
    assert response.status_code == 200
