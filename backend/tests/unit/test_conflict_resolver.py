"""
=============================================================================
BESIKTNINGSAPP BACKEND - CONFLICT RESOLVER TESTS
=============================================================================
Unit tests for conflict resolution service.
"""

import pytest
from app.services.conflict_resolver import ConflictResolver


def test_lww_server_wins():
    """Test Last Write Wins with server winning."""
    server_state = {
        'description': 'Server version',
        'updated_at': '2026-01-29T13:00:00Z'
    }
    client_changes = {
        'description': 'Client version',
        'updated_at': '2026-01-29T12:00:00Z'
    }
    
    result = ConflictResolver.resolve_conflict(
        server_state,
        client_changes,
        strategy='LWW'
    )
    
    assert result['resolved'] == True
    assert result['winner'] == 'server'
    assert result['state'] == server_state


def test_lww_client_wins():
    """Test Last Write Wins with client winning."""
    server_state = {
        'description': 'Server version',
        'updated_at': '2026-01-29T12:00:00Z'
    }
    client_changes = {
        'description': 'Client version',
        'updated_at': '2026-01-29T13:00:00Z'
    }
    
    result = ConflictResolver.resolve_conflict(
        server_state,
        client_changes,
        strategy='LWW'
    )
    
    assert result['resolved'] == True
    assert result['winner'] == 'client'
    assert result['state'] == client_changes


def test_manual_resolution():
    """Test manual conflict resolution."""
    server_state = {'description': 'Server version'}
    client_changes = {'description': 'Client version'}
    
    result = ConflictResolver.resolve_conflict(
        server_state,
        client_changes,
        strategy='manual'
    )
    
    assert result['resolved'] == False
    assert 'conflict' in result
    assert result['conflict']['server_state'] == server_state
    assert result['conflict']['client_changes'] == client_changes
    assert result['conflict']['requires_manual_resolution'] == True


def test_merge_fields_client_wins():
    """Test field-level merge with client_wins strategy."""
    server_state = {
        'field1': 'server_value1',
        'field2': 'server_value2'
    }
    client_changes = {
        'field1': 'client_value1',
        'field2': 'client_value2'
    }
    
    merged = ConflictResolver.merge_fields(
        server_state,
        client_changes,
        field_strategies={'field1': 'client_wins', 'field2': 'client_wins'}
    )
    
    assert merged['field1'] == 'client_value1'
    assert merged['field2'] == 'client_value2'


def test_merge_fields_server_wins():
    """Test field-level merge with server_wins strategy."""
    server_state = {
        'field1': 'server_value1',
        'field2': 'server_value2'
    }
    client_changes = {
        'field1': 'client_value1',
        'field2': 'client_value2'
    }
    
    merged = ConflictResolver.merge_fields(
        server_state,
        client_changes,
        field_strategies={'field1': 'server_wins', 'field2': 'server_wins'}
    )
    
    assert merged['field1'] == 'server_value1'
    assert merged['field2'] == 'server_value2'


def test_merge_fields_mixed_strategies():
    """Test field-level merge with mixed strategies."""
    server_state = {
        'name': 'Server Name',
        'description': 'Server Description',
        'status': 'draft'
    }
    client_changes = {
        'name': 'Client Name',
        'description': 'Client Description',
        'status': 'final'
    }
    
    merged = ConflictResolver.merge_fields(
        server_state,
        client_changes,
        field_strategies={
            'name': 'client_wins',
            'description': 'server_wins',
            'status': 'client_wins'
        }
    )
    
    assert merged['name'] == 'Client Name'
    assert merged['description'] == 'Server Description'
    assert merged['status'] == 'final'


def test_lww_missing_timestamps():
    """Test LWW with missing timestamps (defaults to server)."""
    server_state = {'description': 'Server version'}
    client_changes = {'description': 'Client version'}
    
    result = ConflictResolver.resolve_conflict(
        server_state,
        client_changes,
        strategy='LWW'
    )
    
    assert result['resolved'] == True
    assert result['winner'] == 'server'


def test_merge_fields_default_lww():
    """Test merge with default LWW for unspecified fields."""
    server_state = {
        'field1': 'server1',
        'field2': 'server2'
    }
    client_changes = {
        'field1': 'client1',
        'field2': 'client2'
    }
    
    # No field_strategies specified - defaults to LWW (which defaults to client)
    merged = ConflictResolver.merge_fields(
        server_state,
        client_changes
    )
    
    # Default behavior: client wins
    assert merged['field1'] == 'client1'
    assert merged['field2'] == 'client2'
