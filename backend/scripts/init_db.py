#!/usr/bin/env python3
"""Initialize database with tables."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db

def main():
    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("✓ Database initialized!")

if __name__ == '__main__':
    main()
