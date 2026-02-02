"""Unit tests for validators."""
from app.utils.validators import validate_uuid, validate_email_format

def test_validate_uuid():
    assert validate_uuid('550e8400-e29b-41d4-a716-446655440000')
    assert not validate_uuid('invalid')
