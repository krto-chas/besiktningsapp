"""
=============================================================================
BESIKTNINGSAPP BACKEND - S3/MinIO STORAGE SERVICE
=============================================================================
S3-compatible storage implementation for production use.

Supports:
- AWS S3
- MinIO (self-hosted S3-compatible storage)
- DigitalOcean Spaces
- Any S3-compatible storage

Features:
- Presigned URLs for direct upload/download
- Bucket lifecycle management
- Multipart uploads (future)
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional
from datetime import timedelta

from app.config import Config
from app.utils.errors import StorageError


class S3Storage:
    """S3/MinIO storage service."""
    
    def __init__(self):
        """Initialize S3 client."""
        # S3 Configuration from environment
        self.bucket_name = Config.S3_BUCKET_NAME
        self.region = Config.S3_REGION
        self.endpoint_url = Config.S3_ENDPOINT_URL  # For MinIO
        
        # Initialize boto3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=Config.S3_ACCESS_KEY_ID,
                aws_secret_access_key=Config.S3_SECRET_ACCESS_KEY,
            )
            
            # Verify bucket exists
            self._ensure_bucket()
            
        except NoCredentialsError:
            raise StorageError(
                "S3 credentials not found. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
                operation='init'
            )
        except Exception as e:
            raise StorageError(
                f"Failed to initialize S3 storage: {str(e)}",
                operation='init'
            )
    
    def _ensure_bucket(self):
        """Ensure bucket exists, create if not."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            else:
                raise
    
    # =========================================================================
    # IMAGES
    # =========================================================================
    
    def save_image(self, storage_key: str, content: bytes) -> str:
        """
        Save image to S3.
        
        Args:
            storage_key: S3 key (e.g., "20260203/uuid.jpg")
            content: Image bytes
        
        Returns:
            S3 path (s3://bucket/key)
        
        Raises:
            StorageError: If upload fails
        """
        try:
            # Full S3 key
            s3_key = f"images/{storage_key}"
            
            # Determine content type
            content_type = self._get_content_type(storage_key)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
            )
            
            return f"s3://{self.bucket_name}/{s3_key}"
            
        except ClientError as e:
            raise StorageError(
                f"Failed to save image to S3: {str(e)}",
                operation='save_image'
            )
    
    def read_image(self, storage_key: str) -> bytes:
        """
        Read image from S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            Image bytes
        
        Raises:
            FileNotFoundError: If file not found
            StorageError: If read fails
        """
        try:
            s3_key = f"images/{storage_key}"
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"Image not found: {storage_key}")
            raise StorageError(
                f"Failed to read image from S3: {str(e)}",
                operation='read_image'
            )
    
    def delete_image(self, storage_key: str) -> bool:
        """
        Delete image from S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            True if deleted
        
        Raises:
            StorageError: If delete fails
        """
        try:
            s3_key = f"images/{storage_key}"
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return True
            
        except ClientError as e:
            raise StorageError(
                f"Failed to delete image from S3: {str(e)}",
                operation='delete_image'
            )
    
    def image_exists(self, storage_key: str) -> bool:
        """
        Check if image exists in S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            True if exists
        """
        try:
            s3_key = f"images/{storage_key}"
            
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return True
            
        except ClientError:
            return False
    
    # =========================================================================
    # PDFs
    # =========================================================================
    
    def save_pdf(self, storage_key: str, content: bytes) -> str:
        """
        Save PDF to S3.
        
        Args:
            storage_key: S3 key (e.g., "pdfs/20260203/inspection_1_v1.pdf")
            content: PDF bytes
        
        Returns:
            S3 path
        
        Raises:
            StorageError: If upload fails
        """
        try:
            # Ensure key starts with pdfs/
            if not storage_key.startswith('pdfs/'):
                storage_key = f"pdfs/{storage_key}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=content,
                ContentType='application/pdf',
            )
            
            return f"s3://{self.bucket_name}/{storage_key}"
            
        except ClientError as e:
            raise StorageError(
                f"Failed to save PDF to S3: {str(e)}",
                operation='save_pdf'
            )
    
    def read_pdf(self, storage_key: str) -> bytes:
        """
        Read PDF from S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            PDF bytes
        
        Raises:
            FileNotFoundError: If file not found
            StorageError: If read fails
        """
        try:
            # Ensure key starts with pdfs/
            if not storage_key.startswith('pdfs/'):
                storage_key = f"pdfs/{storage_key}"
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"PDF not found: {storage_key}")
            raise StorageError(
                f"Failed to read PDF from S3: {str(e)}",
                operation='read_pdf'
            )
    
    def delete_pdf(self, storage_key: str) -> bool:
        """
        Delete PDF from S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            True if deleted
        
        Raises:
            StorageError: If delete fails
        """
        try:
            # Ensure key starts with pdfs/
            if not storage_key.startswith('pdfs/'):
                storage_key = f"pdfs/{storage_key}"
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            return True
            
        except ClientError as e:
            raise StorageError(
                f"Failed to delete PDF from S3: {str(e)}",
                operation='delete_pdf'
            )
    
    def pdf_exists(self, storage_key: str) -> bool:
        """
        Check if PDF exists in S3.
        
        Args:
            storage_key: S3 key
        
        Returns:
            True if exists
        """
        try:
            # Ensure key starts with pdfs/
            if not storage_key.startswith('pdfs/'):
                storage_key = f"pdfs/{storage_key}"
            
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            return True
            
        except ClientError:
            return False
    
    # =========================================================================
    # PRESIGNED URLs
    # =========================================================================
    
    def generate_presigned_upload(
        self,
        storage_key: str,
        expires_in: int = 3600
    ) -> dict:
        """
        Generate presigned URL for direct upload.
        
        Args:
            storage_key: S3 key
            expires_in: URL expiry in seconds
        
        Returns:
            Dictionary with 'url' and 'fields'
        
        Raises:
            StorageError: If generation fails
        """
        try:
            s3_key = f"images/{storage_key}"
            
            # Determine content type
            content_type = self._get_content_type(storage_key)
            
            # Generate presigned POST
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 0, 10485760]  # Max 10 MB
                ],
                ExpiresIn=expires_in
            )
            
            return response
            
        except ClientError as e:
            raise StorageError(
                f"Failed to generate presigned upload URL: {str(e)}",
                operation='generate_presigned_upload'
            )
    
    def generate_presigned_url(
        self,
        storage_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate presigned URL for download.
        
        Args:
            storage_key: S3 key (with or without images/ prefix)
            expires_in: URL expiry in seconds
        
        Returns:
            Presigned download URL
        
        Raises:
            StorageError: If generation fails
        """
        try:
            # Add prefix if not present
            if not storage_key.startswith(('images/', 'pdfs/')):
                storage_key = f"images/{storage_key}"
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key
                },
                ExpiresIn=expires_in
            )
            
            return url
            
        except ClientError as e:
            raise StorageError(
                f"Failed to generate presigned download URL: {str(e)}",
                operation='generate_presigned_url'
            )
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get content type from filename.
        
        Args:
            filename: Filename with extension
        
        Returns:
            MIME type
        """
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def get_storage_info(self) -> dict:
        """
        Get storage usage information.
        
        Returns:
            Dictionary with storage stats
        """
        try:
            # List all objects
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_size = 0
            images_size = 0
            pdfs_size = 0
            object_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    size = obj['Size']
                    total_size += size
                    object_count += 1
                    
                    if obj['Key'].startswith('images/'):
                        images_size += size
                    elif obj['Key'].startswith('pdfs/'):
                        pdfs_size += size
            
            return {
                'backend': 's3',
                'bucket': self.bucket_name,
                'region': self.region,
                'endpoint': self.endpoint_url,
                'object_count': object_count,
                'images_size_bytes': images_size,
                'images_size_mb': round(images_size / (1024 * 1024), 2),
                'pdfs_size_bytes': pdfs_size,
                'pdfs_size_mb': round(pdfs_size / (1024 * 1024), 2),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
            }
            
        except ClientError as e:
            raise StorageError(
                f"Failed to get storage info: {str(e)}",
                operation='get_storage_info'
            )
    
    def cleanup_old_files(self, days: int = 90):
        """
        Delete files older than specified days.
        
        Args:
            days: Delete files older than this many days
        
        Raises:
            StorageError: If cleanup fails
        """
        from datetime import datetime, timezone
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # List all objects
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            deleted_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'] < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        deleted_count += 1
            
            return deleted_count
            
        except ClientError as e:
            raise StorageError(
                f"Failed to cleanup old files: {str(e)}",
                operation='cleanup_old_files'
            )