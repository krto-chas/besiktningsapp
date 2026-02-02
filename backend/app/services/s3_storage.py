"""
=============================================================================
BESIKTNINGSAPP BACKEND - S3 STORAGE
=============================================================================
S3/MinIO storage implementation (for production).
"""

from typing import Optional, BinaryIO, Tuple
from datetime import datetime, timedelta
import io

from flask import current_app
import boto3
from botocore.exceptions import ClientError

from app.services.storage_service import StorageService, StorageMetadata


class S3Storage(StorageService):
    """S3/MinIO storage implementation."""
    
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        Initialize S3 storage.
        
        Args:
            endpoint_url: S3 endpoint URL (for MinIO)
            access_key: AWS access key ID
            secret_key: AWS secret access key
            bucket_name: S3 bucket name
            region: AWS region
            use_ssl: Use SSL for connections
        """
        self.endpoint_url = endpoint_url or current_app.config.get("S3_ENDPOINT_URL")
        self.access_key = access_key or current_app.config.get("S3_ACCESS_KEY_ID")
        self.secret_key = secret_key or current_app.config.get("S3_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or current_app.config.get("S3_BUCKET_NAME")
        self.region = region or current_app.config.get("S3_REGION", "us-east-1")
        self.use_ssl = use_ssl if use_ssl is not None else current_app.config.get("S3_USE_SSL", True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            use_ssl=self.use_ssl
        )
    
    def store(
        self,
        file: BinaryIO,
        storage_key: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> StorageMetadata:
        """Store file to S3."""
        # Calculate checksum
        checksum = self.calculate_checksum(file)
        
        # Upload to S3
        file.seek(0)
        extra_args = {
            'ContentType': content_type,
            'Metadata': metadata or {}
        }
        
        self.s3_client.upload_fileobj(
            file,
            self.bucket_name,
            storage_key,
            ExtraArgs=extra_args
        )
        
        # Get object info
        response = self.s3_client.head_object(
            Bucket=self.bucket_name,
            Key=storage_key
        )
        
        return StorageMetadata(
            storage_key=storage_key,
            size_bytes=response['ContentLength'],
            content_type=content_type,
            checksum=checksum,
            url=self.get_url(storage_key)
        )
    
    def retrieve(self, storage_key: str) -> Tuple[BinaryIO, StorageMetadata]:
        """Retrieve file from S3."""
        try:
            # Get object
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            
            # Read into BytesIO
            file = io.BytesIO(response['Body'].read())
            
            # Calculate checksum
            checksum = self.calculate_checksum(file)
            file.seek(0)
            
            metadata = StorageMetadata(
                storage_key=storage_key,
                size_bytes=response['ContentLength'],
                content_type=response.get('ContentType', 'application/octet-stream'),
                checksum=checksum,
                url=self.get_url(storage_key)
            )
            
            return file, metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {storage_key}")
            raise
    
    def delete(self, storage_key: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except ClientError:
            return False
    
    def exists(self, storage_key: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except ClientError:
            return False
    
    def get_url(self, storage_key: str, expires_in: Optional[int] = None) -> str:
        """Get presigned URL for file."""
        if expires_in is None:
            expires_in = current_app.config.get("S3_PRESIGNED_URL_EXPIRATION", 3600)
        
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': storage_key
            },
            ExpiresIn=expires_in
        )
        
        return url
    
    def generate_presigned_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> dict:
        """Generate presigned URL for direct upload."""
        presigned_data = self.s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=storage_key,
            Fields={'Content-Type': content_type},
            Conditions=[
                {'Content-Type': content_type},
                ['content-length-range', 1, 10485760]  # 1 byte to 10MB
            ],
            ExpiresIn=expires_in
        )
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        return {
            "upload_url": presigned_data['url'],
            "fields": presigned_data['fields'],
            "storage_key": storage_key,
            "expires_at": expires_at.isoformat() + "Z"
        }
    
    def health_check(self) -> bool:
        """Check if S3 is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False
