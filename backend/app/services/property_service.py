"""
=============================================================================
BESIKTNINGSAPP BACKEND - PROPERTY SERVICE
=============================================================================
Business logic for Property (Fastighet) operations.

Includes:
- CRUD operations with validation
- Optimistic locking (revision-based)
- Sync support (upsert, modified_since)
- Search and filtering
- Batch operations
- Soft delete support
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from app.models import Property
from app.extensions import db
from app.utils.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


class PropertyService:
    """Business logic for properties."""

    # =========================================================================
    # CREATE
    # =========================================================================

    @staticmethod
    def create_property(data: dict, user_id: int) -> Property:
        """
        Create new property.

        Args:
            data: Property data (from Pydantic schema):
                - property_type: str (required)
                - designation: str (required)
                - address: str (required)
                - postal_code: str (optional)
                - city: str (optional)
                - owner: str (optional)
                - num_apartments: int (optional)
                - num_premises: int (optional)
                - construction_year: int (optional)
                - client_id: str (optional, for offline sync)
            user_id: ID of creating user

        Returns:
            Created Property instance

        Raises:
            ValidationError: If business rules violated
            ConflictError: If duplicate client_id exists
        """
        # Validate business rules
        PropertyService._validate_property_data(data, is_update=False)

        # Check for duplicate client_id if provided
        if data.get('client_id'):
            existing = PropertyService.get_by_client_id(data['client_id'])
            if existing:
                raise ConflictError(
                    f"Property with client_id {data['client_id']} already exists"
                )

        # Create property instance
        property_obj = Property(
            property_type=data['property_type'],
            designation=data['designation'],
            address=data['address'],
            postal_code=data.get('postal_code'),
            city=data.get('city'),
            owner=data.get('owner'),
            num_apartments=data.get('num_apartments'),
            num_premises=data.get('num_premises'),
            construction_year=data.get('construction_year'),
            client_id=data.get('client_id'),
            created_by_id=user_id,
            revision=1,
        )

        try:
            db.session.add(property_obj)
            db.session.commit()
            db.session.refresh(property_obj)
            return property_obj
        except IntegrityError as e:
            db.session.rollback()
            raise ValidationError(f"Database constraint violation: {str(e)}")

    # =========================================================================
    # READ
    # =========================================================================

    @staticmethod
    def get_property(property_id: int) -> Property:
        """
        Get property by ID.

        Args:
            property_id: Property ID

        Returns:
            Property instance

        Raises:
            NotFoundError: If property not found or deleted
        """
        property_obj = Property.query.filter_by(
            id=property_id,
            deleted_at=None
        ).first()

        if not property_obj:
            raise NotFoundError(f"Property with id {property_id} not found")

        return property_obj

    @staticmethod
    def get_by_client_id(client_id: str) -> Optional[Property]:
        """
        Get property by client_id (for sync operations).

        Args:
            client_id: Client-generated UUID

        Returns:
            Property instance or None
        """
        return Property.query.filter_by(
            client_id=client_id,
            deleted_at=None
        ).first()

    @staticmethod
    def get_properties_by_ids(property_ids: List[int]) -> List[Property]:
        """
        Get multiple properties by IDs.

        Args:
            property_ids: List of property IDs

        Returns:
            List of Property instances
        """
        return Property.query.filter(
            Property.id.in_(property_ids),
            Property.deleted_at.is_(None)
        ).all()

    @staticmethod
    def get_user_properties(
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Property], int]:
        """
        Get properties created by specific user.

        Args:
            user_id: User ID
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (properties list, total count)
        """
        query = Property.query.filter_by(
            created_by_id=user_id,
            deleted_at=None
        )

        total = query.count()
        properties = query.order_by(
            Property.created_at.desc()
        ).limit(limit).offset(offset).all()

        return properties, total

    @staticmethod
    def list_properties(
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> Tuple[List[Property], int]:
        """
        List all properties with pagination.

        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            user_id: Optional filter by creating user

        Returns:
            Tuple of (properties list, total count)
        """
        query = Property.query.filter_by(deleted_at=None)

        if user_id:
            query = query.filter_by(created_by_id=user_id)

        total = query.count()
        properties = query.order_by(
            Property.created_at.desc()
        ).limit(limit).offset(offset).all()

        return properties, total

    @staticmethod
    def search_properties(
        search_term: str,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> Tuple[List[Property], int]:
        """
        Search properties by designation, address, city, or owner.

        Args:
            search_term: Search string
            limit: Maximum results to return
            offset: Number of results to skip
            user_id: Optional filter by creating user

        Returns:
            Tuple of (properties list, total count)
        """
        query = Property.query.filter_by(deleted_at=None)

        if user_id:
            query = query.filter_by(created_by_id=user_id)

        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Property.designation.ilike(pattern),
                    Property.address.ilike(pattern),
                    Property.city.ilike(pattern),
                    Property.owner.ilike(pattern)
                )
            )

        total = query.count()
        properties = query.order_by(
            Property.created_at.desc()
        ).limit(limit).offset(offset).all()

        return properties, total

    @staticmethod
    def filter_properties(
        property_type: Optional[str] = None,
        city: Optional[str] = None,
        min_apartments: Optional[int] = None,
        max_apartments: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Property], int]:
        """
        Filter properties by criteria.

        Args:
            property_type: Filter by property type
            city: Filter by city
            min_apartments: Minimum number of apartments
            max_apartments: Maximum number of apartments
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (properties list, total count)
        """
        query = Property.query.filter_by(deleted_at=None)

        if property_type:
            query = query.filter_by(property_type=property_type)

        if city:
            query = query.filter_by(city=city)

        if min_apartments is not None:
            query = query.filter(Property.num_apartments >= min_apartments)

        if max_apartments is not None:
            query = query.filter(Property.num_apartments <= max_apartments)

        total = query.count()
        properties = query.order_by(
            Property.created_at.desc()
        ).limit(limit).offset(offset).all()

        return properties, total

    # =========================================================================
    # UPDATE
    # =========================================================================

    @staticmethod
    def update_property(
        property_id: int,
        data: dict,
        base_revision: int
    ) -> Property:
        """
        Update property with optimistic locking.

        Args:
            property_id: Property ID
            data: Update data (only changed fields)
            base_revision: Client's current revision

        Returns:
            Updated Property instance

        Raises:
            NotFoundError: If property not found
            ConflictError: If revision mismatch
            ValidationError: If validation fails
        """
        property_obj = PropertyService.get_property(property_id)

        # Check revision for optimistic locking
        if property_obj.revision != base_revision:
            raise ConflictError(
                f"Revision conflict. Expected revision {base_revision}, "
                f"but current revision is {property_obj.revision}. "
                f"Property was modified by another user."
            )

        # Validate business rules (allow partial updates)
        PropertyService._validate_property_data(data, is_update=True)

        # Update fields
        updatable_fields = [
            'property_type', 'designation', 'address', 'postal_code',
            'city', 'owner', 'num_apartments', 'num_premises',
            'construction_year'
        ]

        for key, value in data.items():
            if key in updatable_fields:
                setattr(property_obj, key, value)

        # Increment revision
        property_obj.revision += 1
        property_obj.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            db.session.refresh(property_obj)
            return property_obj
        except IntegrityError as e:
            db.session.rollback()
            raise ValidationError(f"Database constraint violation: {str(e)}")

    # =========================================================================
    # DELETE
    # =========================================================================

    @staticmethod
    def delete_property(property_id: int) -> bool:
        """
        Soft delete property.

        Args:
            property_id: Property ID

        Returns:
            True if deleted, False if already deleted

        Raises:
            NotFoundError: If property not found
        """
        property_obj = Property.query.filter_by(id=property_id).first()

        if not property_obj:
            raise NotFoundError(f"Property with id {property_id} not found")

        if property_obj.deleted_at:
            return False  # Already deleted

        property_obj.deleted_at = datetime.utcnow()
        property_obj.revision += 1

        db.session.commit()
        return True

    @staticmethod
    def restore_property(property_id: int) -> Property:
        """
        Restore soft-deleted property.

        Args:
            property_id: Property ID

        Returns:
            Restored Property instance

        Raises:
            NotFoundError: If property not found
            ValidationError: If property not deleted
        """
        property_obj = Property.query.filter_by(id=property_id).first()

        if not property_obj:
            raise NotFoundError(f"Property with id {property_id} not found")

        if not property_obj.deleted_at:
            raise ValidationError("Property is not deleted")

        property_obj.deleted_at = None
        property_obj.revision += 1
        property_obj.updated_at = datetime.utcnow()

        db.session.commit()
        db.session.refresh(property_obj)
        return property_obj

    # =========================================================================
    # SYNC SUPPORT
    # =========================================================================

    @staticmethod
    def upsert_from_sync(data: dict, user_id: int) -> Tuple[Property, bool]:
        """
        Create or update property from sync push.

        This is used during offline sync to handle both new properties
        created offline and updates to existing properties.

        Args:
            data: Property data including client_id
            user_id: ID of syncing user

        Returns:
            Tuple of (property, was_created)

        Raises:
            ValidationError: If data invalid
        """
        client_id = data.get('client_id')

        if not client_id:
            raise ValidationError("client_id required for sync operations")

        # Validate data
        PropertyService._validate_property_data(data, is_update=False)

        # Try to find existing by client_id
        existing = PropertyService.get_by_client_id(client_id)

        if existing:
            # Update existing (no revision check for sync upsert)
            updatable_fields = [
                'property_type', 'designation', 'address', 'postal_code',
                'city', 'owner', 'num_apartments', 'num_premises',
                'construction_year', 'revision'
            ]

            for key in updatable_fields:
                if key in data:
                    setattr(existing, key, data[key])

            existing.updated_at = datetime.utcnow()

            db.session.commit()
            db.session.refresh(existing)
            return existing, False
        else:
            # Create new
            property_obj = Property(
                property_type=data['property_type'],
                designation=data['designation'],
                address=data['address'],
                postal_code=data.get('postal_code'),
                city=data.get('city'),
                owner=data.get('owner'),
                num_apartments=data.get('num_apartments'),
                num_premises=data.get('num_premises'),
                construction_year=data.get('construction_year'),
                client_id=client_id,
                created_by_id=user_id,
                revision=data.get('revision', 1),
            )

            db.session.add(property_obj)
            db.session.commit()
            db.session.refresh(property_obj)
            return property_obj, True

    @staticmethod
    def get_modified_since(
        since: datetime,
        user_id: Optional[int] = None
    ) -> List[Property]:
        """
        Get properties modified since timestamp (for sync pull).

        Args:
            since: Get properties modified after this time (UTC)
            user_id: Optional filter by creating user

        Returns:
            List of modified properties (including soft-deleted)
        """
        query = Property.query.filter(
            Property.updated_at > since
        )

        if user_id:
            query = query.filter_by(created_by_id=user_id)

        return query.order_by(Property.updated_at.asc()).all()

    @staticmethod
    def get_sync_status(property_id: int) -> dict:
        """
        Get sync status for a property.

        Args:
            property_id: Property ID

        Returns:
            Dictionary with sync metadata
        """
        property_obj = PropertyService.get_property(property_id)

        return {
            'id': property_obj.id,
            'client_id': property_obj.client_id,
            'revision': property_obj.revision,
            'created_at': property_obj.created_at.isoformat(),
            'updated_at': property_obj.updated_at.isoformat(),
            'deleted_at': property_obj.deleted_at.isoformat() if property_obj.deleted_at else None,
        }

    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================

    @staticmethod
    def get_statistics(user_id: Optional[int] = None) -> dict:
        """
        Get property statistics.

        Args:
            user_id: Optional filter by user

        Returns:
            Dictionary with statistics
        """
        query = Property.query.filter_by(deleted_at=None)

        if user_id:
            query = query.filter_by(created_by_id=user_id)

        total = query.count()

        # Count by type
        types = db.session.query(
            Property.property_type,
            db.func.count(Property.id)
        ).filter_by(deleted_at=None)

        if user_id:
            types = types.filter_by(created_by_id=user_id)

        types = types.group_by(Property.property_type).all()

        # Count by city (top 10)
        cities = db.session.query(
            Property.city,
            db.func.count(Property.id)
        ).filter(
            Property.deleted_at.is_(None),
            Property.city.isnot(None)
        )

        if user_id:
            cities = cities.filter_by(created_by_id=user_id)

        cities = cities.group_by(Property.city).order_by(
            db.func.count(Property.id).desc()
        ).limit(10).all()

        return {
            'total_properties': total,
            'by_type': {t[0]: t[1] for t in types},
            'top_cities': {c[0]: c[1] for c in cities if c[0]},
        }

    # =========================================================================
    # VALIDATION
    # =========================================================================

    @staticmethod
    def _validate_property_data(data: dict, is_update: bool = False) -> None:
        """
        Validate business rules.

        Args:
            data: Property data to validate
            is_update: True if updating, False if creating

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for create
        if not is_update:
            required = ['property_type', 'designation', 'address']
            missing = [f for f in required if f not in data or not data[f]]
            if missing:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing)}"
                )

        # Validate property_type
        if 'property_type' in data:
            valid_types = [
                'flerbostadshus', 'villa', 'radhus', 'parhus',
                'kedjehus', 'kontor', 'lokal', 'industribyggnad',
                'lager', 'skola', 'förskola', 'vårdbyggnad',
                'hotell', 'restaurang', 'garage', 'övrigt'
            ]
            prop_type = data['property_type'].lower().strip()
            if prop_type not in valid_types:
                raise ValidationError(
                    f"Invalid property_type '{prop_type}'. "
                    f"Must be one of: {', '.join(valid_types)}"
                )

        # Validate num_apartments range
        if 'num_apartments' in data and data['num_apartments'] is not None:
            num_apts = data['num_apartments']
            if num_apts < 0 or num_apts > 10000:
                raise ValidationError(
                    "num_apartments must be between 0 and 10000"
                )

        # Validate num_premises range
        if 'num_premises' in data and data['num_premises'] is not None:
            num_prem = data['num_premises']
            if num_prem < 0 or num_prem > 10000:
                raise ValidationError(
                    "num_premises must be between 0 and 10000"
                )

        # Validate construction_year
        if 'construction_year' in data and data['construction_year'] is not None:
            year = data['construction_year']
            current_year = datetime.now().year
            if year < 1500 or year > current_year + 5:
                raise ValidationError(
                    f"construction_year must be between 1500 and {current_year + 5}"
                )

        # Validate string lengths
        string_fields = {
            'property_type': 100,
            'designation': 255,
            'address': 500,
            'postal_code': 20,
            'city': 100,
            'owner': 255,
        }

        for field, max_len in string_fields.items():
            if field in data and data[field]:
                if len(str(data[field])) > max_len:
                    raise ValidationError(
                        f"{field} exceeds maximum length of {max_len} characters"
                    )

        # Validate postal code format (Swedish format: 123 45 or 12345)
        if 'postal_code' in data and data['postal_code']:
            import re
            postal = data['postal_code'].strip()
            if not re.match(r'^\d{3}\s?\d{2}$', postal):
                raise ValidationError(
                    "postal_code must be in format: 123 45 or 12345"
                )

    @staticmethod
    def check_revision_conflict(property_obj: Property, base_revision: int) -> bool:
        """
        Check if revision matches (for optimistic locking).

        Args:
            property_obj: Property instance
            base_revision: Client's current revision

        Returns:
            True if conflict exists, False otherwise
        """
        return property_obj.revision != base_revision

    @staticmethod
    def can_delete(property_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if property can be deleted.

        Args:
            property_id: Property ID

        Returns:
            Tuple of (can_delete, reason_if_not)
        """
        property_obj = PropertyService.get_property(property_id)

        # Check if property has inspections
        from app.models import Inspection
        inspection_count = Inspection.query.filter_by(
            property_id=property_id,
            deleted_at=None
        ).count()

        if inspection_count > 0:
            return False, f"Property has {inspection_count} active inspection(s)"

        return True, None