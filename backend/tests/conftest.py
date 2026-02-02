"""
=============================================================================
BESIKTNINGSAPP BACKEND - PYTEST FIXTURES
=============================================================================
Shared pytest fixtures for testing.
"""

import pytest
import tempfile
import shutil
from datetime import datetime

from app import create_app
from app.extensions import db as _db
from app.models import User, Property, Inspection


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    # Push application context
    ctx = app.app_context()
    ctx.push()
    
    yield app
    
    ctx.pop()


@pytest.fixture(scope='session')
def database(app):
    """Create database for testing."""
    _db.create_all()
    
    yield _db
    
    _db.drop_all()


@pytest.fixture(scope='function')
def db_session(database):
    """Create a new database session for a test."""
    connection = database.engine.connect()
    transaction = connection.begin()
    
    session = database.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    database.session = session
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app, db_session):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        role="inspector",
        active=True
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create admin user."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        role="admin",
        active=True
    )
    user.set_password("admin123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = response.json['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_property(db_session):
    """Create sample property."""
    property = Property(
        property_type="flerbostadshus",
        designation="TEST 1:1",
        address="Testgatan 1",
        city="Stockholm",
        num_apartments=12
    )
    db_session.add(property)
    db_session.commit()
    return property


@pytest.fixture
def sample_inspection(db_session, sample_property, test_user):
    """Create sample inspection."""
    inspection = Inspection(
        property_id=sample_property.id,
        inspector_id=test_user.id,
        date=datetime.utcnow().date(),
        status="draft"
    )
    db_session.add(inspection)
    db_session.commit()
    return inspection
