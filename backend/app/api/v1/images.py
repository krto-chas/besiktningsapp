"""
=============================================================================
BESIKTNINGSAPP BACKEND - IMAGES API
=============================================================================
REST API endpoints for Image upload and management.

Endpoints:
- POST   /images/upload             - Direct upload
- POST   /images/presigned          - Generate presigned upload URL
- POST   /images/:id/complete       - Mark presigned upload as complete
- GET    /images/:id                - Get image metadata
- GET    /images/:id/download       - Download image
- GET    /images/:id/thumbnail      - Download thumbnail
- DELETE /images/:id                - Delete image
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from io import BytesIO

from app.services.image_service import ImageService
from app.schemas import (
    ImageResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
    ImageCompleteRequest,
    StandardResponse,
    ErrorResponse,
)
from app.utils.errors import NotFoundError, ValidationError
from app.utils.decorators import rate_limit

images_bp = Blueprint('images', __name__, url_prefix='/images')


# =============================================================================
# UPLOAD
# =============================================================================

@images_bp.route('/upload', methods=['POST'])
@jwt_required()
@rate_limit("20/minute")
def upload_image():
    """
    Direct image upload.

    Request:
        - Content-Type: multipart/form-data
        - file: image file (required)
        - client_id: UUID (optional, for sync)

    Returns:
        201: Image uploaded successfully
        400: Validation error (invalid file, too large, etc.)
        429: Rate limit exceeded
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify(ErrorResponse.validation_error(
                "No file provided. Use 'file' field in multipart/form-data"
            ).model_dump()), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify(ErrorResponse.validation_error(
                "No file selected"
            ).model_dump()), 400
        
        # Get optional client_id
        client_id = request.form.get('client_id')
        
        # Get current user
        user_id = get_jwt_identity()
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Upload image
        image_obj = ImageService.upload_image(
            file=file,
            filename=filename,
            user_id=user_id,
            client_id=client_id
        )
        
        # Return response
        response = ImageResponse.model_validate(image_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 201
        
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@images_bp.route('/presigned', methods=['POST'])
@jwt_required()
@rate_limit("30/minute")
def generate_presigned_upload():
    """
    Generate presigned URL for direct upload to storage.

    This allows mobile clients to upload directly to S3/MinIO without
    going through the backend, reducing server load and improving speed.

    Request Body (PresignedUploadRequest):
        {
            "filename": "photo.jpg"
        }

    Returns:
        200: Presigned upload URL and metadata
        400: Validation error
        501: Not supported with local storage
    """
    try:
        # Validate request body
        data = PresignedUploadRequest(**request.get_json())
        
        # Get current user
        user_id = get_jwt_identity()
        
        # Secure filename
        filename = secure_filename(data.filename)
        
        # Generate presigned URL
        presigned_data = ImageService.generate_presigned_upload(
            filename=filename,
            user_id=user_id,
            expires_in=3600  # 1 hour
        )
        
        # Return response
        response = PresignedUploadResponse(**presigned_data)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except ValidationError as e:
        if "not supported" in str(e).lower():
            return jsonify(ErrorResponse(
                error={
                    'code': 'not_implemented',
                    'message': str(e)
                }
            ).model_dump()), 501
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@images_bp.route('/<int:image_id>/complete', methods=['POST'])
@jwt_required()
@rate_limit("30/minute")
def complete_upload(image_id):
    """
    Mark presigned upload as complete.

    Called by client after successful presigned upload to update metadata.

    Path Parameters:
        - image_id: int

    Request Body (ImageCompleteRequest):
        {
            "file_size": 1048576,
            "width": 1920,
            "height": 1080,
            "checksum": "sha256-hash"
        }

    Returns:
        200: Upload completed
        400: Validation error
        404: Image not found
    """
    try:
        # Validate request body
        data = ImageCompleteRequest(**request.get_json())
        
        # Complete upload
        image_obj = ImageService.complete_upload(
            image_id=image_id,
            file_size=data.file_size,
            width=data.width,
            height=data.height,
            checksum=data.checksum
        )
        
        # Return response
        response = ImageResponse.model_validate(image_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except ValidationError as e:
        return jsonify(ErrorResponse.validation_error(str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# READ
# =============================================================================

@images_bp.route('/<int:image_id>', methods=['GET'])
@jwt_required()
def get_image(image_id):
    """
    Get image metadata.

    Path Parameters:
        - image_id: int

    Returns:
        200: Image metadata
        404: Image not found
    """
    try:
        image_obj = ImageService.get_image(image_id)
        response = ImageResponse.model_validate(image_obj)
        return jsonify(StandardResponse(data=response).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@images_bp.route('/<int:image_id>/url', methods=['GET'])
@jwt_required()
def get_image_url(image_id):
    """
    Get download URL for image.

    Path Parameters:
        - image_id: int

    Query Parameters:
        - thumbnail: bool (default false)

    Returns:
        200: Download URL
        404: Image not found
    """
    try:
        thumbnail = request.args.get('thumbnail', 'false').lower() == 'true'
        
        url = ImageService.get_image_url(
            image_id=image_id,
            thumbnail=thumbnail
        )
        
        return jsonify(StandardResponse(
            data={'url': url}
        ).model_dump()), 200
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


@images_bp.route('/<int:image_id>/download', methods=['GET'])
@jwt_required()
def download_image(image_id):
    """
    Download image file.

    Path Parameters:
        - image_id: int

    Query Parameters:
        - thumbnail: bool (default false)

    Returns:
        200: Image file
        404: Image not found
    """
    try:
        thumbnail = request.args.get('thumbnail', 'false').lower() == 'true'
        
        # Get image content
        content, mime_type = ImageService.get_image_content(
            image_id=image_id,
            thumbnail=thumbnail
        )
        
        # Get image metadata for filename
        image_obj = ImageService.get_image(image_id)
        filename = image_obj.filename
        
        if thumbnail:
            # Add _thumb suffix to filename
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, 'jpg')
            filename = f"{name}_thumb.{ext}"
        
        # Send file
        return send_file(
            BytesIO(content),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# DELETE
# =============================================================================

@images_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
@rate_limit("10/minute")
def delete_image(image_id):
    """
    Soft delete image.

    Path Parameters:
        - image_id: int

    Query Parameters:
        - delete_from_storage: bool (default true)

    Returns:
        200: Image deleted
        404: Image not found
    """
    try:
        # Get query parameter
        delete_from_storage = request.args.get(
            'delete_from_storage',
            'true'
        ).lower() == 'true'
        
        # Delete image
        deleted = ImageService.delete_image(
            image_id=image_id,
            delete_from_storage=delete_from_storage
        )
        
        if deleted:
            return jsonify(StandardResponse(
                data={'message': 'Image deleted successfully'}
            ).model_dump()), 200
        else:
            return jsonify(StandardResponse(
                data={'message': 'Image already deleted'}
            ).model_dump()), 200
            
    except NotFoundError as e:
        return jsonify(ErrorResponse.not_found(str(e)).model_dump()), 404
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# STATISTICS
# =============================================================================

@images_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    Get image statistics.

    Query Parameters:
        - user_id: int (optional, filter by user)

    Returns:
        200: Statistics data
    """
    try:
        user_id = request.args.get('user_id', type=int)
        stats = ImageService.get_statistics(user_id=user_id)
        return jsonify(StandardResponse(data=stats).model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse.internal_error(str(e)).model_dump()), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@images_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(ErrorResponse.not_found().model_dump()), 404


@images_bp.errorhandler(413)
def too_large(error):
    """Handle 413 Payload Too Large errors."""
    return jsonify(ErrorResponse.validation_error(
        "File too large. Maximum size: 10MB"
    ).model_dump()), 413


@images_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify(ErrorResponse.internal_error().model_dump()), 500