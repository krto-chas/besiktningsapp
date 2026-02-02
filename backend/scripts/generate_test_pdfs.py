#!/usr/bin/env python3
"""Generate test PDFs for inspections."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.models import Inspection
from app.services.pdf_service import PDFService

def main():
    app = create_app()
    with app.app_context():
        inspections = Inspection.query.limit(5).all()
        print(f"Generating PDFs for {len(inspections)} inspections...")
        
        for insp in inspections:
            try:
                pdf = PDFService.generate_pdf(insp.id, insp.inspector_id or 1, status='draft')
                print(f"✓ PDF v{pdf.version_number} for inspection {insp.id}")
            except Exception as e:
                print(f"✗ Failed for inspection {insp.id}: {e}")

if __name__ == '__main__':
    main()
