"""Property business logic service."""
from typing import List, Optional
from sqlalchemy import or_
from app.models import Property
from app.extensions import db


class PropertyService:
    """Business logic for properties."""
    
    @staticmethod
    def search_properties(search_term: str, limit: int = 50, offset: int = 0) -> tuple[List[Property], int]:
        """Search properties by designation, address, or city."""
        query = Property.query
        
        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Property.designation.ilike(pattern),
                    Property.address.ilike(pattern),
                    Property.city.ilike(pattern)
                )
            )
        
        total = query.count()
        properties = query.order_by(Property.created_at.desc()).limit(limit).offset(offset).all()
        
        return properties, total
    
    @staticmethod
    def get_by_client_id(client_id: str) -> Optional[Property]:
        """Get property by client_id."""
        return Property.query.filter_by(client_id=client_id).first()
