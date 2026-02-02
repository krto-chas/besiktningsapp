#!/usr/bin/env python3
"""Seed database with test data."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, StandardDefect

def main():
    app = create_app()
    with app.app_context():
        print("Seeding data...")
        
        # Admin user
        if not User.query.filter_by(email='admin@besiktningsapp.se').first():
            admin = User(email='admin@besiktningsapp.se', name='Admin', role='admin', active=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Admin created")
        
        # Inspector
        if not User.query.filter_by(email='inspector@besiktningsapp.se').first():
            inspector = User(email='inspector@besiktningsapp.se', name='Inspector', role='inspector', active=True)
            inspector.set_password('inspector123')
            db.session.add(inspector)
            print("✓ Inspector created")
        
        # Standard defects
        defects = [
            {'code': 'VF01', 'title': 'Från-luftsventil saknas', 'description': 'Ventil saknas', 'severity': 'high'},
            {'code': 'VF02', 'title': 'Ventil defekt', 'description': 'Ventil är trasig', 'severity': 'medium'},
        ]
        for d in defects:
            if not StandardDefect.query.filter_by(code=d['code']).first():
                defect = StandardDefect(**d, remedy='Åtgärda enligt BBR')
                db.session.add(defect)
        
        db.session.commit()
        print("✓ Data seeded!")

if __name__ == '__main__':
    main()
