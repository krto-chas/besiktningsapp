"""
=============================================================================
BESIKTNINGSAPP BACKEND - PDF SERVICE
=============================================================================
Business logic for PDF generation and versioning.

Includes:
- PDF generation with WeasyPrint (HTML -> PDF)
- Swedish OVK inspection report format
- PDF versioning (immutable versions)
- Template-based generation
- Storage integration
- Metadata tracking
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import hashlib
from io import BytesIO

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import PDFVersion, Inspection, Apartment, Defect, Image, Measurement
from app.extensions import db
from app.utils.errors import ValidationError, NotFoundError
from app.config import Config


class PDFService:
    """Business logic for PDF generation."""

    # PDF status values
    VALID_STATUSES = ['generating', 'completed', 'failed']

    # Template directory
    TEMPLATE_DIR = 'app/templates/pdf'

    # =========================================================================
    # PDF GENERATION
    # =========================================================================

    @staticmethod
    def generate_inspection_pdf(
        inspection_id: int,
        user_id: int,
        include_photos: bool = True,
        template: str = 'standard'
    ) -> PDFVersion:
        """
        Generate PDF report for inspection.

        Args:
            inspection_id: Inspection ID
            user_id: Requesting user ID
            include_photos: Include defect photos
            template: Template name ('standard', 'minimal', etc.)

        Returns:
            Created PDFVersion instance

        Raises:
            NotFoundError: If inspection not found
            ValidationError: If data invalid
        """
        # Get inspection with relationships
        inspection = Inspection.query.filter_by(
            id=inspection_id,
            deleted_at=None
        ).first()

        if not inspection:
            raise NotFoundError(f"Inspection with id {inspection_id} not found")

        # Create pending PDF version record
        pdf_version = PDFVersion(
            inspection_id=inspection_id,
            version=PDFService._get_next_version(inspection_id),
            status='generating',
            generated_by_id=user_id,
            template=template,
            include_photos=include_photos,
        )

        db.session.add(pdf_version)
        db.session.commit()

        try:
            # Gather data for PDF
            if template == 'ovk':
                data = PDFService._gather_ovk_data(inspection, include_photos=include_photos)
            else:
                data = PDFService._gather_inspection_data(
                    inspection,
                    include_photos=include_photos
                )

            # Generate HTML from template
            html_content = PDFService._render_template(template, data)

            # Convert HTML to PDF
            pdf_content = PDFService._html_to_pdf(html_content)

            # Calculate checksum
            checksum = hashlib.sha256(pdf_content).hexdigest()

            # Generate storage key
            storage_key = PDFService._generate_storage_key(
                inspection_id,
                pdf_version.version
            )

            # Save to storage
            storage = PDFService._get_storage()
            storage_path = storage.save_pdf(storage_key, pdf_content)

            # Update PDF version record
            pdf_version.status = 'completed'
            pdf_version.file_size = len(pdf_content)
            pdf_version.checksum = checksum
            pdf_version.storage_key = storage_key
            pdf_version.storage_path = storage_path

            db.session.commit()
            db.session.refresh(pdf_version)

            return pdf_version

        except Exception as e:
            # Mark as failed
            pdf_version.status = 'failed'
            pdf_version.error_message = str(e)
            db.session.commit()
            raise ValidationError(f"PDF generation failed: {str(e)}")

    # =========================================================================
    # READ
    # =========================================================================

    @staticmethod
    def get_pdf_version(pdf_id: int) -> PDFVersion:
        """
        Get PDF version by ID.

        Args:
            pdf_id: PDF version ID

        Returns:
            PDFVersion instance

        Raises:
            NotFoundError: If PDF not found
        """
        pdf_obj = PDFVersion.query.filter_by(id=pdf_id).first()

        if not pdf_obj:
            raise NotFoundError(f"PDF version with id {pdf_id} not found")

        return pdf_obj

    @staticmethod
    def get_inspection_pdfs(
        inspection_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[PDFVersion], int]:
        """
        Get all PDF versions for inspection.

        Args:
            inspection_id: Inspection ID
            limit: Maximum results
            offset: Number to skip

        Returns:
            Tuple of (PDF versions list, total count)
        """
        query = PDFVersion.query.filter_by(inspection_id=inspection_id)

        total = query.count()
        pdfs = query.order_by(
            PDFVersion.version.desc()
        ).limit(limit).offset(offset).all()

        return pdfs, total

    @staticmethod
    def get_latest_pdf(inspection_id: int) -> Optional[PDFVersion]:
        """
        Get latest completed PDF for inspection.

        Args:
            inspection_id: Inspection ID

        Returns:
            Latest PDFVersion or None
        """
        return PDFVersion.query.filter_by(
            inspection_id=inspection_id,
            status='completed'
        ).order_by(
            PDFVersion.version.desc()
        ).first()

    # =========================================================================
    # DOWNLOAD
    # =========================================================================

    @staticmethod
    def get_pdf_url(pdf_id: int) -> str:
        """
        Get URL to download PDF.

        Args:
            pdf_id: PDF version ID

        Returns:
            Download URL

        Raises:
            NotFoundError: If PDF not found
            ValidationError: If PDF not completed
        """
        pdf_obj = PDFService.get_pdf_version(pdf_id)

        if pdf_obj.status != 'completed':
            raise ValidationError(f"PDF not ready. Status: {pdf_obj.status}")

        storage = PDFService._get_storage()

        if hasattr(storage, 'generate_presigned_url'):
            # S3/MinIO - generate presigned download URL
            return storage.generate_presigned_url(pdf_obj.storage_key, expires_in=3600)
        else:
            # Local storage - return API endpoint
            return f"/api/v1/pdf/{pdf_id}/download"

    @staticmethod
    def get_pdf_content(pdf_id: int) -> Tuple[bytes, str]:
        """
        Get PDF file content.

        Args:
            pdf_id: PDF version ID

        Returns:
            Tuple of (file_content, filename)

        Raises:
            NotFoundError: If PDF not found or file missing
            ValidationError: If PDF not completed
        """
        pdf_obj = PDFService.get_pdf_version(pdf_id)

        if pdf_obj.status != 'completed':
            raise ValidationError(f"PDF not ready. Status: {pdf_obj.status}")

        storage = PDFService._get_storage()

        try:
            content = storage.read_pdf(pdf_obj.storage_key)

            # Generate filename
            inspection = pdf_obj.inspection
            property_obj = inspection.property if inspection else None
            designation = property_obj.designation if property_obj else "Unknown"

            # Clean designation for filename
            clean_designation = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in designation
            )

            filename = f"Besiktning_{clean_designation}_v{pdf_obj.version}.pdf"

            return content, filename

        except FileNotFoundError:
            raise NotFoundError(f"PDF file not found in storage: {pdf_obj.storage_key}")

    # =========================================================================
    # DELETE
    # =========================================================================

    @staticmethod
    def delete_pdf_version(pdf_id: int, delete_from_storage: bool = True) -> bool:
        """
        Delete PDF version.

        Args:
            pdf_id: PDF version ID
            delete_from_storage: If True, also delete from storage

        Returns:
            True if deleted

        Raises:
            NotFoundError: If PDF not found
        """
        pdf_obj = PDFVersion.query.filter_by(id=pdf_id).first()

        if not pdf_obj:
            raise NotFoundError(f"PDF version with id {pdf_id} not found")

        # Delete from storage
        if delete_from_storage and pdf_obj.storage_key:
            storage = PDFService._get_storage()
            try:
                storage.delete_pdf(pdf_obj.storage_key)
            except Exception as e:
                print(f"Error deleting PDF from storage: {e}")

        # Delete database record
        db.session.delete(pdf_obj)
        db.session.commit()

        return True

    # =========================================================================
    # DATA GATHERING
    # =========================================================================

    @staticmethod
    def _gather_inspection_data(
        inspection: Inspection,
        include_photos: bool = True
    ) -> Dict[str, Any]:
        """
        Gather all data needed for PDF generation.

        Args:
            inspection: Inspection instance
            include_photos: Include defect photos

        Returns:
            Dictionary with all PDF data
        """
        # Get property
        property_obj = inspection.property

        # Get apartments with rooms and defects
        apartments = Apartment.query.filter_by(
            inspection_id=inspection.id,
            deleted_at=None
        ).order_by(Apartment.apartment_number).all()

        apartments_data = []
        total_defects = 0
        defects_by_severity = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}

        for apartment in apartments:
            # Get defects for this apartment
            defects = Defect.query.filter_by(
                apartment_id=apartment.id,
                deleted_at=None
            ).order_by(Defect.room_index, Defect.code).all()

            defects_data = []
            for defect in defects:
                defect_dict = {
                    'code': defect.code,
                    'title': defect.title,
                    'description': defect.description,
                    'remedy': defect.remedy,
                    'severity': defect.severity.value,
                    'room_index': defect.room_index,
                    'room_type': PDFService._get_room_type(apartment.rooms, defect.room_index),
                    'photos': []
                }

                # Count severity
                defects_by_severity[defect.severity.value] += 1
                total_defects += 1

                # Get photos if requested
                if include_photos and defect.photos:
                    for photo_meta in defect.photos:
                        if isinstance(photo_meta, dict) and photo_meta.get('image_id'):
                            image = Image.query.filter_by(
                                id=photo_meta['image_id'],
                                deleted_at=None
                            ).first()
                            if image:
                                defect_dict['photos'].append({
                                    'filename': image.filename,
                                    'storage_key': image.storage_key,
                                })

                defects_data.append(defect_dict)

            apartments_data.append({
                'apartment_number': apartment.apartment_number,
                'rooms': apartment.rooms,
                'notes': apartment.notes,
                'defects': defects_data,
                'defect_count': len(defects_data),
            })

        # Format active time
        active_hours = inspection.active_time_seconds // 3600
        active_minutes = (inspection.active_time_seconds % 3600) // 60

        # Build data dictionary
        data = {
            'inspection': {
                'id': inspection.id,
                'date': inspection.date.strftime('%Y-%m-%d'),
                'status': inspection.status,
                'active_time_seconds': inspection.active_time_seconds,
                'active_time_formatted': f"{active_hours}h {active_minutes}min",
                'notes': inspection.notes,
            },
            'property': {
                'designation': property_obj.designation,
                'property_type': property_obj.property_type,
                'address': property_obj.address,
                'postal_code': property_obj.postal_code,
                'city': property_obj.city,
                'owner': property_obj.owner,
                'num_apartments': property_obj.num_apartments,
                'construction_year': property_obj.construction_year,
            },
            'inspector': {
                'name': inspection.inspector.name if inspection.inspector else 'N/A',
                'email': inspection.inspector.email if inspection.inspector else 'N/A',
                'certification_number': inspection.inspector.certification_number if inspection.inspector else None,
            },
            'apartments': apartments_data,
            'summary': {
                'total_apartments': len(apartments_data),
                'total_defects': total_defects,
                'defects_by_severity': defects_by_severity,
            },
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        }

        return data

    # OVK position prefixes – maps position code prefix to checklist section
    _OVK_POSITIONS = {
        '1.1', '1.2', '1.3', '1.4', '1.5',
        '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '2.10',
        '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '3.10',
        '4.1', '4.2', '4.3', '4.4', '4.5', '4.6',
    }

    @staticmethod
    def _gather_ovk_data(
        inspection: Inspection,
        include_photos: bool = True,
    ) -> Dict[str, Any]:
        """
        Gather data for the OVK template (A/B/L/Intyg blanketter).

        Returns a dict consumed by ovk.html.
        """
        property_obj = inspection.property
        inspector = inspection.inspector

        # ── Property ─────────────────────────────────────────────────────────
        property_data = {
            'designation':      property_obj.designation,
            'property_name':    getattr(property_obj, 'property_name', None),
            'address':          property_obj.address,
            'postal_code':      property_obj.postal_code,
            'city':             property_obj.city,
            'owner':            property_obj.owner,
            'manager':          getattr(property_obj, 'manager', None),
            'num_apartments':   property_obj.num_apartments,
            'num_locals':       getattr(property_obj, 'num_locals', None),
            'bra_m2':           getattr(property_obj, 'bra_m2', None),
            'construction_year': property_obj.construction_year,
            'activity':         getattr(property_obj, 'activity', None),
        }

        # ── Inspector ─────────────────────────────────────────────────────────
        inspector_data: Dict[str, Any] = {'name': 'N/A', 'email': 'N/A'}
        if inspector:
            inspector_data = {
                'name':                    inspector.name,
                'email':                   inspector.email,
                'company_name':            inspector.company_name,
                'phone':                   inspector.phone,
                'certification_org':       inspector.certification_org,
                'certification_number':    inspector.certification_number,
                'certification_valid_until': inspector.certification_valid_until,
                'competence':              inspector.competence,
            }

        # ── Inspection (OVK fields) ────────────────────────────────────────
        energy_measures: List[int] = []
        if inspection.energy_saving_measures:
            try:
                energy_measures = [
                    int(x.strip())
                    for x in inspection.energy_saving_measures.split(',')
                    if x.strip().isdigit()
                ]
            except (ValueError, AttributeError):
                pass

        inspection_data = {
            'id':                   inspection.id,
            'date':                 inspection.date.strftime('%Y-%m-%d') if inspection.date else '–',
            'status':               inspection.status.value if inspection.status else 'draft',
            'notes':                inspection.notes,
            'ovk_result':           inspection.ovk_result.value if inspection.ovk_result else None,
            'next_inspection_date': inspection.next_inspection_date.strftime('%Y-%m-%d')
                                    if inspection.next_inspection_date else None,
            'reinspection_date':    inspection.reinspection_date.strftime('%Y-%m-%d')
                                    if inspection.reinspection_date else None,
            'system_number':        inspection.system_number,
            'system_type':          inspection.system_type.value if inspection.system_type else None,
            'inspection_category':  inspection.inspection_category,
            'energy_saving_measures': energy_measures,
            # Climate and user_comments stored in notes (no separate fields yet)
            'climate':              None,
            'user_comments':        None,
            # system_components: placeholder (no dedicated model yet)
            'system_components':    [],
        }

        # ── Defects → OVK position map ────────────────────────────────────
        all_defects = (
            Defect.query
            .join(Apartment)
            .filter(
                Apartment.inspection_id == inspection.id,
                Defect.deleted_at.is_(None),
            )
            .all()
        )

        defects_by_pos: Dict[str, List[Dict]] = {}
        defects_other: List[Dict] = []

        for defect in all_defects:
            d_dict = {
                'code':        defect.code,
                'title':       defect.title,
                'description': defect.description,
                'remedy':      defect.remedy,
                'severity':    defect.severity.value,
            }
            # Match code against OVK position (exact prefix match)
            matched = False
            if defect.code:
                # code might be "2.3", "2.3.1", "3.7 Luftflöden" – try prefix
                for pos in PDFService._OVK_POSITIONS:
                    if defect.code.startswith(pos):
                        defects_by_pos.setdefault(pos, []).append(d_dict)
                        matched = True
                        break
            if not matched:
                defects_other.append(d_dict)

        # ── Airflow rows (L-blankett) ─────────────────────────────────────
        flow_measurements = (
            Measurement.query
            .filter_by(inspection_id=inspection.id)
            .filter(Measurement.direction.isnot(None))
            .filter(Measurement.deleted_at.is_(None))
            .order_by(Measurement.sort_key, Measurement.id)
            .all()
        )

        # Group T+F by room (sort_key = room number)
        room_map: Dict[str, Dict] = {}
        for m in flow_measurements:
            key = m.sort_key or str(m.id)
            if key not in room_map:
                room_map[key] = {
                    'room_number': m.sort_key,
                    'room_name':   m.room_name,
                    'T_proj': None, 'T_value': None, 'T_method': None,
                    'F_proj': None, 'F_value': None, 'F_method': None,
                }
            dir_key = m.direction.value if m.direction else None
            if dir_key == 'T':
                room_map[key]['T_value']  = m.value
                room_map[key]['T_proj']   = m.projected_value
                room_map[key]['T_method'] = m.measurement_method
                if m.room_name:
                    room_map[key]['room_name'] = m.room_name
            elif dir_key == 'F':
                room_map[key]['F_value']  = m.value
                room_map[key]['F_proj']   = m.projected_value
                room_map[key]['F_method'] = m.measurement_method
                if m.room_name:
                    room_map[key]['room_name'] = m.room_name

        airflow_rows = list(room_map.values())

        return {
            'property':      property_data,
            'inspector':     inspector_data,
            'inspection':    inspection_data,
            'defects_by_pos': defects_by_pos,
            'defects_other':  defects_other,
            'airflow_rows':   airflow_rows,
            'generated_at':  datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'app_version':   '1.0',
        }

    @staticmethod
    def _get_room_type(rooms: List[dict], room_index: int) -> str:
        """
        Get room type from room index.

        Args:
            rooms: List of room dictionaries
            room_index: Room index

        Returns:
            Room type string
        """
        if not rooms:
            return 'Okänt rum'

        for room in rooms:
            if room.get('index') == room_index:
                return room.get('type', 'Okänt rum')

        return 'Okänt rum'

    # =========================================================================
    # TEMPLATE RENDERING
    # =========================================================================

    @staticmethod
    def _render_template(template_name: str, data: Dict[str, Any]) -> str:
        """
        Render HTML template with data.

        Args:
            template_name: Template name ('standard', 'minimal', etc.)
            data: Template data

        Returns:
            Rendered HTML string
        """
        # Setup Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(PDFService.TEMPLATE_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Load template
        template_file = f"{template_name}.html"
        template = env.get_template(template_file)

        # Render template
        html_content = template.render(**data)

        return html_content

    # =========================================================================
    # PDF CONVERSION
    # =========================================================================

    @staticmethod
    def _html_to_pdf(html_content: str) -> bytes:
        """
        Convert HTML to PDF using WeasyPrint.

        Args:
            html_content: HTML string

        Returns:
            PDF bytes
        """
        # CSS for styling
        css_content = """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "Sida " counter(page) " av " counter(pages);
                font-size: 10pt;
            }
        }

        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
        }

        h1 {
            color: #2c3e50;
            font-size: 20pt;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }

        h2 {
            color: #34495e;
            font-size: 16pt;
            margin-top: 20px;
        }

        h3 {
            color: #7f8c8d;
            font-size: 13pt;
            margin-top: 15px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }

        th, td {
            border: 1px solid #bdc3c7;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #ecf0f1;
            font-weight: bold;
        }

        .severity-low {
            color: #27ae60;
        }

        .severity-medium {
            color: #f39c12;
        }

        .severity-high {
            color: #e74c3c;
        }

        .defect-box {
            border: 1px solid #bdc3c7;
            padding: 10px;
            margin: 10px 0;
            page-break-inside: avoid;
        }

        .summary-box {
            background-color: #ecf0f1;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }

        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            font-size: 9pt;
            color: #7f8c8d;
        }
        """

        css = CSS(string=css_content)

        # Convert to PDF
        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file, stylesheets=[css])

        return pdf_file.getvalue()

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _get_next_version(inspection_id: int) -> int:
        """
        Get next version number for inspection.

        Args:
            inspection_id: Inspection ID

        Returns:
            Next version number
        """
        max_version = db.session.query(
            db.func.max(PDFVersion.version)
        ).filter_by(inspection_id=inspection_id).scalar()

        return (max_version or 0) + 1

    @staticmethod
    def _generate_storage_key(inspection_id: int, version: int) -> str:
        """
        Generate storage key for PDF.

        Args:
            inspection_id: Inspection ID
            version: PDF version

        Returns:
            Storage key
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        return f"pdfs/{timestamp}/inspection_{inspection_id}_v{version}.pdf"

    @staticmethod
    def _get_storage():
        """
        Get storage service instance.

        Returns:
            Storage service
        """
        storage_backend = Config.STORAGE_BACKEND

        if storage_backend == 's3':
            from app.services.s3_storage import S3Storage
            return S3Storage()
        else:
            from app.services.local_storage import LocalStorage
            return LocalStorage()

    # =========================================================================
    # STATISTICS
    # =========================================================================

    @staticmethod
    def get_statistics(inspection_id: Optional[int] = None) -> dict:
        """
        Get PDF generation statistics.

        Args:
            inspection_id: Optional filter by inspection

        Returns:
            Dictionary with statistics
        """
        query = PDFVersion.query

        if inspection_id:
            query = query.filter_by(inspection_id=inspection_id)

        total = query.count()
        completed = query.filter_by(status='completed').count()
        failed = query.filter_by(status='failed').count()

        total_size = db.session.query(
            db.func.sum(PDFVersion.file_size)
        ).filter_by(status='completed')

        if inspection_id:
            total_size = total_size.filter_by(inspection_id=inspection_id)

        total_size = total_size.scalar() or 0

        return {
            'total_versions': total,
            'completed': completed,
            'failed': failed,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }