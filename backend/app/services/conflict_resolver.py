"""
=============================================================================
BESIKTNINGSAPP BACKEND - CONFLICT RESOLVER
=============================================================================
Conflict resolution strategies for sync operations.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ConflictResolver:
    """Conflict resolution service for sync."""
    
    @staticmethod
    def resolve_conflict(
        server_state: Dict[str, Any],
        client_changes: Dict[str, Any],
        strategy: str = "LWW"
    ) -> Dict[str, Any]:
        """
        Resolve conflict between server and client state.
        
        Args:
            server_state: Current server state
            client_changes: Client's attempted changes
            strategy: Resolution strategy (LWW, manual, etc.)
            
        Returns:
            Resolved state or conflict info for manual resolution
        """
        if strategy == "LWW":
            return ConflictResolver._last_write_wins(server_state, client_changes)
        elif strategy == "manual":
            return ConflictResolver._manual_resolution(server_state, client_changes)
        else:
            return ConflictResolver._last_write_wins(server_state, client_changes)
    
    @staticmethod
    def _last_write_wins(
        server_state: Dict[str, Any],
        client_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Last Write Wins strategy.
        
        Compare timestamps and accept the most recent change.
        """
        server_time = server_state.get("updated_at")
        client_time = client_changes.get("updated_at")
        
        if client_time and server_time:
            if client_time > server_time:
                # Client wins
                return {
                    "resolved": True,
                    "winner": "client",
                    "state": client_changes
                }
            else:
                # Server wins
                return {
                    "resolved": True,
                    "winner": "server",
                    "state": server_state
                }
        
        # Default to server if timestamps missing
        return {
            "resolved": True,
            "winner": "server",
            "state": server_state
        }
    
    @staticmethod
    def _manual_resolution(
        server_state: Dict[str, Any],
        client_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manual resolution - return conflict for client to resolve.
        """
        return {
            "resolved": False,
            "conflict": {
                "server_state": server_state,
                "client_changes": client_changes,
                "requires_manual_resolution": True
            }
        }
    
    @staticmethod
    def merge_fields(
        server_state: Dict[str, Any],
        client_changes: Dict[str, Any],
        field_strategies: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Merge specific fields with different strategies.
        
        Args:
            server_state: Server state
            client_changes: Client changes
            field_strategies: Per-field resolution strategies
            
        Returns:
            Merged state
        """
        merged = server_state.copy()
        field_strategies = field_strategies or {}
        
        for field, value in client_changes.items():
            strategy = field_strategies.get(field, "LWW")
            
            if strategy == "client_wins":
                merged[field] = value
            elif strategy == "server_wins":
                merged[field] = server_state.get(field)
            elif strategy == "LWW":
                # Compare timestamps if available
                merged[field] = value  # Default to client for simplicity
        
        return merged
