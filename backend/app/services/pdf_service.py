"""
=============================================================================
BESIKTNINGSAPP BACKEND - PDF SERVICE
=============================================================================
PDF generation and versioning service.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import io

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models import PDFVersion, Inspection
from app.extensions import db


class PDFService:
    """PDF generation and versioning service."""
    
    @staticmethod
    def generate_pdf(
        inspection_id: int,
        user_id: int,
        status: str = "draft",
        options: Optional[Dict[str, Any]] = None
    ) -> PDFVersion:
        """
        Generate PDF for inspection.
        
        Args:
            inspection_id: Inspection ID
            user_id: User ID (creator)
            status: PDF status (draft/final)
            options: Generation options
            
        Returns:
            PDFVersion object
        """
        inspection = Inspection.query.get(inspection_id)
        if not inspection:
            raise ValueError("Inspection not found")
        
        # Get next version number
        last_version = PDFVersion.query.filter_by(
            inspection_id=inspection_id
        ).order_by(PDFVersion.version_number.desc()).first()
        
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Generate PDF content
        pdf_buffer = PDFService._generate_pdf_content(inspection, options or {})
        
        # TODO: Store PDF using storage_service
        storage_key = f"pdfs/{datetime.utcnow().year}/{datetime.utcnow().month}/inspection_{inspection_id}_v{version_number}.pdf"
        filename = f"besiktning_{inspection_id}_v{version_number}.pdf"
        
        # Calculate checksum
        import hashlib
        pdf_buffer.seek(0)
        checksum = f"sha256:{hashlib.sha256(pdf_buffer.read()).hexdigest()}"
        pdf_buffer.seek(0)
        
        size_bytes = len(pdf_buffer.getvalue())
        
        # Create PDF version record
        pdf_version = PDFVersion(
            inspection_id=inspection_id,
            created_by_user_id=user_id,
            version_number=version_number,
            status=status,
            storage_key=storage_key,
            filename=filename,
            size_bytes=size_bytes,
            checksum=checksum
        )
        
        db.session.add(pdf_version)
        db.session.commit()
        
        return pdf_version
    
    @staticmethod
    def _generate_pdf_content(inspection: Inspection, options: Dict[str, Any]) -> io.BytesIO:
        """
        Generate PDF content (basic implementation).
        
        Args:
            inspection: Inspection object
            options: Generation options
            
        Returns:
            BytesIO buffer with PDF content
        """
        buffer = io.BytesIO()
        
        # Create PDF
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Title
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 50, "Besiktningsprotokoll")
        
        # Inspection info
        p.setFont("Helvetica", 12)
        y = height - 100
        p.drawString(50, y, f"Besiktnings-ID: {inspection.id}")
        y -= 20
        p.drawString(50, y, f"Datum: {inspection.date}")
        y -= 20
        p.drawString(50, y, f"Status: {inspection.status}")
        
        # TODO: Add apartments, defects, measurements, images
        # This is a basic placeholder implementation
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
