"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTION SERVICE
=============================================================================
Business logic for Inspection (Besiktning) operations.

Includes:
- CRUD operations with validation
- Optimistic locking (revision-based)
- Timer functionality (active_time_seconds)
- Status management (draft, final, archived)
- Property relationship validation
- Sync support (upsert, modified_since)
- Apartment and defect aggregation
"""
from typing import List, Optional, Tuple
from datetime import datetime, date as date_type
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from app.models import Inspection, Property, Apartment, Defect
from app.extensions import db
from app.utils.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


class InspectionService:
    """Business logic for inspections."""

    # Valid inspection statuses
    VALID_STATUSES = ['draft', 'final', 'archived']

    # =========================================================================
    # CREATE
    # =========================================================================

    @staticmethod
    def create_inspection(data: dict, user_id: int) -> Inspection:
        """
        Create new inspection.

        Args:
            data: Inspection data:
                - property_id: int (optional, server reference)
                - property_client_id: str (optional, for offline)
                - date: date (required)
                - active_time_seconds: int (default 0)
                - status: str (default 'draft')
                - notes: str (optional)
                - client_id: str (optional, for offline sync)
            user_id: ID of creating user (inspector)

        Returns:
            Created Inspection instance

        Raises:
            ValidationError: If business rules violated
            NotFoundError: If property not found
            ConflictError: If duplicate client_id
        """
        # Validate business rules
        InspectionService._validate_inspection_data(data, is_update=False)

        # Resolve property (either by property_id or property_client_id)
        property_id = InspectionService._resolve_property(
            data.get('property_id'),
            data.get('property_client_id')
        )

        # Check for duplicate client_id if provided
        if data.get('client_id'):
            existing = InspectionService.get_by_client_id(data['client_id'])
            if existing:
                raise ConflictError(
                    f"Inspection with client_id {data['client_id']} already exists"
                )

        # Create inspection instance
        inspection_obj = Inspection(
            property_id=property_id,
            inspector_id=user_id,
            date=data['date'],
            active_time_seconds=data.get('active_time_seconds', 0),
            status=data.get('status', 'draft'),
            notes=data.get('notes'),
            client_id=data.get('client_id'),
            revision=1,
        )

        try:
            db.session.add(inspection_obj)
            db.session.commit()
            db.session.refresh(inspection_obj)
            return inspection_obj
        except IntegrityError as e:
            db.session.rollback()
            raise ValidationError(f"Database constraint violation: {str(e)}")

    # =========================================================================
    # READ
    # =========================================================================

    @staticmethod
    def get_inspection(inspection_id: int) -> Inspection:
        """
        Get inspection by ID.

        Args:
            inspection_id: Inspection ID

        Returns:
            Inspection instance

        Raises:
            NotFoundError: If inspection not found or deleted
        """
        inspection_obj = Inspection.query.filter_by(
            id=inspection_id,
            deleted_at=None
        ).first()

        if not inspection_obj:
            raise NotFoundError(f"Inspection with id {inspection_id} not found")

        return inspection_obj

    @staticmethod
    def get_by_client_id(client_id: str) -> Optional[Inspection]:
        """
        Get inspection by client_id (for sync operations).

        Args:
            client_id: Client-generated UUID

        Returns:
            Inspection instance or None
        """
        return Inspection.query.filter_by(
            client_id=client_id,
            deleted_at=None
        ).first()

    @staticmethod
    def get_inspections_by_ids(inspection_ids: List[int]) -> List[Inspection]:
        """
        Get multiple inspections by IDs.

        Args:
            inspection_ids: List of inspection IDs

        Returns:
            List of Inspection instances
        """
        return Inspection.query.filter(
            Inspection.id.in_(inspection_ids),
            Inspection.deleted_at.is_(None)
        ).all()

    @staticmethod
    def get_property_inspections(
        property_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Inspection], int]:
        """
        Get all inspections for a property.

        Args:
            property_id: Property ID
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (inspections list, total count)
        """
        query = Inspection.query.filter_by(
            property_id=property_id,
            deleted_at=None
        )

        total = query.count()
        inspections = query.order_by(
            Inspection.date.desc()
        ).limit(limit).offset(offset).all()

        return inspections, total

    @staticmethod
    def get_inspector_inspections(
        inspector_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Inspection], int]:
        """
        Get all inspections by an inspector.

        Args:
            inspector_id: Inspector user ID
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (inspections list, total count)
        """
        query = Inspection.query.filter_by(
            inspector_id=inspector_id,
            deleted_at=None
        )

        total = query.count()
        inspections = query.order_by(
            Inspection.date.desc()
        ).limit(limit).offset(offset).all()

        return inspections, total

    @staticmethod
    def list_inspections(
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        inspector_id: Optional[int] = None
    ) -> Tuple[List[Inspection], int]:
        """
        List all inspections with optional filters.

        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            status: Optional filter by status
            inspector_id: Optional filter by inspector

        Returns:
            Tuple of (inspections list, total count)
        """
        query = Inspection.query.filter_by(deleted_at=None)

        if status:
            query = query.filter_by(status=status)

        if inspector_id:
            query = query.filter_by(inspector_id=inspector_id)

        total = query.count()
        inspections = query.order_by(
            Inspection.date.desc()
        ).limit(limit).offset(offset).all()

        return inspections, total

    @staticmethod
    def search_inspections(
        search_term: str,
        limit: int = 50,
        offset: int = 0,
        inspector_id: Optional[int] = None
    ) -> Tuple[List[Inspection], int]:
        """
        Search inspections by property designation or notes.

        Args:
            search_term: Search string
            limit: Maximum results to return
            offset: Number of results to skip
            inspector_id: Optional filter by inspector

        Returns:
            Tuple of (inspections list, total count)
        """
        # Join with Property to search by designation
        query = db.session.query(Inspection).join(Property).filter(
            Inspection.deleted_at.is_(None)
        )

        if inspector_id:
            query = query.filter(Inspection.inspector_id == inspector_id)

        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Property.designation.ilike(pattern),
                    Inspection.notes.ilike(pattern)
                )
            )

        total = query.count()
        inspections = query.order_by(
            Inspection.date.desc()
        ).limit(limit).offset(offset).all()

        return inspections, total

    # =========================================================================
    # UPDATE
    # =========================================================================

    @staticmethod
    def update_inspection(
        inspection_id: int,
        data: dict,
        base_revision: int
    ) -> Inspection:
        """
        Update inspection with optimistic locking.

        Args:
            inspection_id: Inspection ID
            data: Update data (only changed fields)
            base_revision: Client's current revision

        Returns:
            Updated Inspection instance

        Raises:
            NotFoundError: If inspection not found
            ConflictError: If revision mismatch
            ValidationError: If validation fails
        """
        inspection_obj = InspectionService.get_inspection(inspection_id)

        # Check revision for optimistic locking
        if inspection_obj.revision != base_revision:
            raise ConflictError(
                f"Revision conflict. Expected revision {base_revision}, "
                f"but current revision is {inspection_obj.revision}. "
                f"Inspection was modified by another user."
            )

        # Validate business rules
        InspectionService._validate_inspection_data(data, is_update=True)

        # Update fields
        updatable_fields = [
            'date', 'active_time_seconds', 'status', 'notes'
        ]

        for key in updatable_fields:
            if key in data:
                setattr(inspection_obj, key, data[key])

        # Increment revision
        inspection_obj.revision += 1
        inspection_obj.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            db.session.refresh(inspection_obj)
            return inspection_obj
        except IntegrityError as e:
            db.session.rollback()
            raise ValidationError(f"Database constraint violation: {str(e)}")

    @staticmethod
    def update_active_time(
        inspection_id: int,
        active_time_seconds: int,
        base_revision: int
    ) -> Inspection:
        """
        Update active time (used by timer).

        Args:
            inspection_id: Inspection ID
            active_time_seconds: New active time in seconds
            base_revision: Client's current revision

        Returns:
            Updated Inspection instance

        Raises:
            ValidationError: If time invalid
        """
        if active_time_seconds < 0 or active_time_seconds > 86400:
            raise ValidationError(
                "active_time_seconds must be between 0 and 86400 (24 hours)"
            )

        return InspectionService.update_inspection(
            inspection_id=inspection_id,
            data={'active_time_seconds': active_time_seconds},
            base_revision=base_revision
        )

    @staticmethod
    def change_status(
        inspection_id: int,
        new_status: str,
        base_revision: int
    ) -> Inspection:
        """
        Change inspection status (draft -> final -> archived).

        Args:
            inspection_id: Inspection ID
            new_status: New status ('draft', 'final', 'archived')
            base_revision: Client's current revision

        Returns:
            Updated Inspection instance

        Raises:
            ValidationError: If status transition invalid
        """
        if new_status not in InspectionService.VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{new_status}'. "
                f"Must be one of: {', '.join(InspectionService.VALID_STATUSES)}"
            )

        inspection_obj = InspectionService.get_inspection(inspection_id)

        # Validate status transitions
        current_status = inspection_obj.status

        # Define valid transitions
        valid_transitions = {
            'draft': ['final', 'archived'],
            'final': ['archived'],
            'archived': []  # Cannot change from archived
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Cannot change status from '{current_status}' to '{new_status}'"
            )

        return InspectionService.update_inspection(
            inspection_id=inspection_id,
            data={'status': new_status},
            base_revision=base_revision
        )

    # =========================================================================
    # DELETE
    # =========================================================================

    @staticmethod
    def delete_inspection(inspection_id: int) -> bool:
        """
        Soft delete inspection.

        Args:
            inspection_id: Inspection ID

        Returns:
            True if deleted, False if already deleted

        Raises:
            NotFoundError: If inspection not found
        """
        inspection_obj = Inspection.query.filter_by(id=inspection_id).first()

        if not inspection_obj:
            raise NotFoundError(f"Inspection with id {inspection_id} not found")

        if inspection_obj.deleted_at:
            return False  # Already deleted

        inspection_obj.deleted_at = datetime.utcnow()
        inspection_obj.revision += 1

        db.session.commit()
        return True

    # =========================================================================
    # SYNC SUPPORT
    # =========================================================================

    @staticmethod
    def upsert_from_sync(data: dict, user_id: int) -> Tuple[Inspection, bool]:
        """
        Create or update inspection from sync push.

        Args:
            data: Inspection data including client_id
            user_id: ID of syncing user

        Returns:
            Tuple of (inspection, was_created)

        Raises:
            ValidationError: If data invalid
        """
        client_id = data.get('client_id')

        if not client_id:
            raise ValidationError("client_id required for sync operations")

        # Validate data
        InspectionService._validate_inspection_data(data, is_update=False)

        # Resolve property
        property_id = InspectionService._resolve_property(
            data.get('property_id'),
            data.get('property_client_id')
        )

        # Try to find existing by client_id
        existing = InspectionService.get_by_client_id(client_id)

        if existing:
            # Update existing
            updatable_fields = [
                'date', 'active_time_seconds', 'status', 'notes', 'revision'
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
            inspection_obj = Inspection(
                property_id=property_id,
                inspector_id=user_id,
                date=data['date'],
                active_time_seconds=data.get('active_time_seconds', 0),
                status=data.get('status', 'draft'),
                notes=data.get('notes'),
                client_id=client_id,
                revision=data.get('revision', 1),
            )

            db.session.add(inspection_obj)
            db.session.commit()
            db.session.refresh(inspection_obj)
            return inspection_obj, True

    @staticmethod
    def get_modified_since(
        since: datetime,
        inspector_id: Optional[int] = None
    ) -> List[Inspection]:
        """
        Get inspections modified since timestamp (for sync pull).

        Args:
            since: Get inspections modified after this time (UTC)
            inspector_id: Optional filter by inspector

        Returns:
            List of modified inspections (including soft-deleted)
        """
        query = Inspection.query.filter(
            Inspection.updated_at > since
        )

        if inspector_id:
            query = query.filter_by(inspector_id=inspector_id)

        return query.order_by(Inspection.updated_at.asc()).all()

    # =========================================================================
    # AGGREGATION & STATISTICS
    # =========================================================================

    @staticmethod
    def get_inspection_summary(inspection_id: int) -> dict:
        """
        Get comprehensive summary of inspection.

        Args:
            inspection_id: Inspection ID

        Returns:
            Dictionary with summary data
        """
        inspection_obj = InspectionService.get_inspection(inspection_id)

        # Count apartments
        apartment_count = Apartment.query.filter_by(
            inspection_id=inspection_id,
            deleted_at=None
        ).count()

        # Count defects by severity
        defects = db.session.query(
            Defect.severity,
            db.func.count(Defect.id)
        ).join(Apartment).filter(
            Apartment.inspection_id == inspection_id,
            Defect.deleted_at.is_(None)
        ).group_by(Defect.severity).all()

        total_defects = sum(count for _, count in defects)
        defects_by_severity = {severity.value: count for severity, count in defects}

        return {
            'inspection_id': inspection_obj.id,
            'property_id': inspection_obj.property_id,
            'date': inspection_obj.date.isoformat(),
            'status': inspection_obj.status,
            'active_time_seconds': inspection_obj.active_time_seconds,
            'active_time_formatted': InspectionService._format_time(
                inspection_obj.active_time_seconds
            ),
            'apartment_count': apartment_count,
            'total_defects': total_defects,
            'defects_by_severity': defects_by_severity,
            'created_at': inspection_obj.created_at.isoformat(),
            'updated_at': inspection_obj.updated_at.isoformat(),
        }

    @staticmethod
    def get_statistics(inspector_id: Optional[int] = None) -> dict:
        """
        Get inspection statistics.

        Args:
            inspector_id: Optional filter by inspector

        Returns:
            Dictionary with statistics
        """
        query = Inspection.query.filter_by(deleted_at=None)

        if inspector_id:
            query = query.filter_by(inspector_id=inspector_id)

        total = query.count()

        # Count by status
        statuses = db.session.query(
            Inspection.status,
            db.func.count(Inspection.id)
        ).filter_by(deleted_at=None)

        if inspector_id:
            statuses = statuses.filter_by(inspector_id=inspector_id)

        statuses = statuses.group_by(Inspection.status).all()

        # Average active time
        avg_time = db.session.query(
            db.func.avg(Inspection.active_time_seconds)
        ).filter_by(deleted_at=None)

        if inspector_id:
            avg_time = avg_time.filter_by(inspector_id=inspector_id)

        avg_time = avg_time.scalar() or 0

        return {
            'total_inspections': total,
            'by_status': {s[0]: s[1] for s in statuses},
            'average_active_time_seconds': int(avg_time),
            'average_active_time_formatted': InspectionService._format_time(int(avg_time)),
        }

    # =========================================================================
    # VALIDATION & HELPERS
    # =========================================================================

    @staticmethod
    def _validate_inspection_data(data: dict, is_update: bool = False) -> None:
        """
        Validate business rules.

        Args:
            data: Inspection data to validate
            is_update: True if updating, False if creating

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for create
        if not is_update:
            required = ['date']
            
            # Either property_id or property_client_id required
            if 'property_id' not in data and 'property_client_id' not in data:
                raise ValidationError(
                    "Either property_id or property_client_id is required"
                )
            
            missing = [f for f in required if f not in data]
            if missing:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing)}"
                )

        # Validate date
        if 'date' in data:
            inspection_date = data['date']
            if isinstance(inspection_date, str):
                try:
                    inspection_date = datetime.fromisoformat(inspection_date).date()
                except ValueError:
                    raise ValidationError("Invalid date format. Use YYYY-MM-DD")
            
            # Check date not too far in future (max 1 year)
            from datetime import timedelta
            max_future = datetime.now().date() + timedelta(days=365)
            if inspection_date > max_future:
                raise ValidationError("Inspection date cannot be more than 1 year in the future")

        # Validate active_time_seconds
        if 'active_time_seconds' in data:
            time = data['active_time_seconds']
            if time < 0 or time > 86400:
                raise ValidationError(
                    "active_time_seconds must be between 0 and 86400 (24 hours)"
                )

        # Validate status
        if 'status' in data:
            status = data['status']
            if status not in InspectionService.VALID_STATUSES:
                raise ValidationError(
                    f"Invalid status '{status}'. "
                    f"Must be one of: {', '.join(InspectionService.VALID_STATUSES)}"
                )

        # Validate notes length
        if 'notes' in data and data['notes']:
            if len(data['notes']) > 2000:
                raise ValidationError("notes cannot exceed 2000 characters")

    @staticmethod
    def _resolve_property(
        property_id: Optional[int],
        property_client_id: Optional[str]
    ) -> int:
        """
        Resolve property ID from either server ID or client ID.

        Args:
            property_id: Server property ID
            property_client_id: Client UUID for property

        Returns:
            Resolved property ID

        Raises:
            NotFoundError: If property not found
            ValidationError: If neither ID provided
        """
        if property_id:
            # Verify property exists
            property_obj = Property.query.filter_by(
                id=property_id,
                deleted_at=None
            ).first()
            
            if not property_obj:
                raise NotFoundError(f"Property with id {property_id} not found")
            
            return property_id

        elif property_client_id:
            # Find by client_id
            property_obj = Property.query.filter_by(
                client_id=property_client_id,
                deleted_at=None
            ).first()
            
            if not property_obj:
                raise NotFoundError(
                    f"Property with client_id {property_client_id} not found"
                )
            
            return property_obj.id

        else:
            raise ValidationError(
                "Either property_id or property_client_id must be provided"
            )

    @staticmethod
    def _format_time(seconds: int) -> str:
        """
        Format seconds as HH:MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def can_delete(inspection_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if inspection can be deleted.

        Args:
            inspection_id: Inspection ID

        Returns:
            Tuple of (can_delete, reason_if_not)
        """
        inspection_obj = InspectionService.get_inspection(inspection_id)

        # Cannot delete final or archived inspections
        if inspection_obj.status in ['final', 'archived']:
            return False, f"Cannot delete inspection with status '{inspection_obj.status}'"

        # Check if has apartments
        apartment_count = Apartment.query.filter_by(
            inspection_id=inspection_id,
            deleted_at=None
        ).count()

        if apartment_count > 0:
            return False, f"Inspection has {apartment_count} apartment(s). Delete apartments first."

        return True, None