"""Inspection business logic service."""
from typing import List, Optional
from datetime import date
from app.models import Inspection, Property
from app.extensions import db


class InspectionService:
    """Business logic for inspections."""
    
    @staticmethod
    def get_by_property(property_id: int, limit: int = 50, offset: int = 0) -> tuple[List[Inspection], int]:
        """Get inspections for a property."""
        query = Inspection.query.filter_by(property_id=property_id)
        total = query.count()
        inspections = query.order_by(Inspection.date.desc()).limit(limit).offset(offset).all()
        return inspections, total
    
    @staticmethod
    def get_by_client_id(client_id: str) -> Optional[Inspection]:
        """Get inspection by client_id."""
        return Inspection.query.filter_by(client_id=client_id).first()
    
    @staticmethod
    def get_active_inspections(user_id: int) -> List[Inspection]:
        """Get active (draft) inspections for user."""
        return Inspection.query.filter_by(
            inspector_id=user_id,
            status="draft"
        ).order_by(Inspection.date.desc()).all()
