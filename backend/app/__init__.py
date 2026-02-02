"""
=============================================================================
BESIKTNINGSAPP BACKEND - APP PACKAGE
=============================================================================
Main application package for the Besiktningsapp backend API.

This package contains:
- Flask application factory (main.py)
- Configuration management (config.py)
- Extensions initialization (extensions.py)
- Domain models (models/)
- API endpoints (api/)
- Business logic (services/)
- Utilities (utils/)
"""

__version__ = "1.0.0"
__author__ = "Besiktningsapp Team"
__all__ = ["create_app"]

from app.main import create_app
