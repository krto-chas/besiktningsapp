"""Test data factories."""
from datetime import date
from app.models import User, Property, Inspection, Apartment, Defect

class UserFactory:
    @staticmethod
    def create(email='user@test.com', **kwargs):
        user = User(
            email=email,
            name=kwargs.get('name', 'Test User'),
            role=kwargs.get('role', 'inspector'),
            active=kwargs.get('active', True)
        )
        user.set_password(kwargs.get('password', 'password123'))
        return user

class PropertyFactory:
    @staticmethod
    def create(**kwargs):
        return Property(
            property_type=kwargs.get('property_type', 'villa'),
            designation=kwargs.get('designation', 'TEST 1:1'),
            address=kwargs.get('address', 'Test St 1'),
            city=kwargs.get('city', 'Test City')
        )

class InspectionFactory:
    @staticmethod
    def create(property_id, **kwargs):
        return Inspection(
            property_id=property_id,
            inspector_id=kwargs.get('inspector_id'),
            date=kwargs.get('date', date.today()),
            status=kwargs.get('status', 'draft')
        )
