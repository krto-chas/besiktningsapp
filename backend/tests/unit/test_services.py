"""Unit tests for services."""
from app.services.auth_service import AuthService

def test_create_token(db_session, test_user):
    token = AuthService.create_token(test_user.id)
    assert isinstance(token, str)
