"""
=============================================================================
BESIKTNINGSAPP BACKEND - APARTMENT MODEL
=============================================================================
Apartment model (Lägenhet).

Represents an apartment within an inspection.
Rooms are stored as JSON array for flexibility.
"""
from __future__ import annotations


from typing import List, Dict, Any

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Apartment(BaseModel):
    """
    Apartment model (Lägenhet).
    
    Attributes:
        inspection_id: Foreign key to Inspection
        apartment_number: Apartment number (e.g., "1201", "A12", "12B")
        rooms: JSON array of rooms with type and index
            Example: [
                {"index": 0, "type": "hall"},
                {"index": 1, "type": "kok"},
                {"index": 2, "type": "vardagsrum"},
                {"index": 3, "type": "sovrum"},
                {"index": 4, "type": "badrum"},
            ]
        notes: Additional notes about the apartment
    """
    
    __tablename__ = "apartments"
    
    # Foreign Key
    inspection_id = Column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Inspection this apartment belongs to",
    )
    
    # Apartment Details
    apartment_number = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Apartment number (e.g., 1201, A12, 12B)",
    )
    
    # Rooms (JSON field)
    rooms = Column(
        JSON,
        nullable=False,
        default=list,
        comment="Array of rooms: [{index: int, type: string}, ...]",
    )
    
    # Notes
    notes = Column(
        String(1000),
        nullable=True,
        comment="Additional notes about the apartment",
    )
    
    # Relationships
    inspection = relationship(
        "Inspection",
        back_populates="apartments",
    )
    
    defects = relationship(
        "Defect",
        back_populates="apartment",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    def get_room_type(self, room_index: int) -> str:
        """
        Get room type by index.
        
        Args:
            room_index: Room index (0-based)
            
        Returns:
            Room type string or "unknown"
        """
        if not self.rooms:
            return "unknown"
        
        for room in self.rooms:
            if room.get("index") == room_index:
                return room.get("type", "unknown")
        
        return "unknown"
    
    def add_room(self, room_type: str) -> int:
        """
        Add a new room.
        
        Args:
            room_type: Type of room (e.g., "kok", "sovrum", "badrum")
            
        Returns:
            Index of the newly added room
        """
        if self.rooms is None:
            self.rooms = []
        
        # Get next index
        next_index = len(self.rooms)
        
        # Add room
        self.rooms.append({
            "index": next_index,
            "type": room_type,
        })
        
        return next_index
    
    def remove_room(self, room_index: int) -> bool:
        """
        Remove a room by index.
        
        Args:
            room_index: Room index to remove
            
        Returns:
            True if removed, False if not found
        """
        if not self.rooms:
            return False
        
        # Find and remove room
        for i, room in enumerate(self.rooms):
            if room.get("index") == room_index:
                self.rooms.pop(i)
                return True
        
        return False
    
    def reorder_rooms(self, new_order: List[int]) -> None:
        """
        Reorder rooms according to new index order.
        
        Args:
            new_order: List of room indices in desired order
        """
        if not self.rooms:
            return
        
        # Create mapping of old index to room
        room_map = {room["index"]: room for room in self.rooms}
        
        # Create new rooms list with updated indices
        new_rooms = []
        for new_index, old_index in enumerate(new_order):
            if old_index in room_map:
                room = room_map[old_index].copy()
                room["index"] = new_index
                new_rooms.append(room)
        
        self.rooms = new_rooms
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Apartment(id={self.id}, number={self.apartment_number}, rooms={len(self.rooms or [])})>"
