"""Unit tests for models."""
from tests.factories import UserFactory, PropertyFactory

def test_user_password(db_session):
    user = UserFactory.create()
    db_session.add(user)
    db_session.commit()
    assert user.check_password('password123')

def test_property_revision(db_session):
    prop = PropertyFactory.create()
    db_session.add(prop)
    db_session.commit()
    assert prop.revision == 1
