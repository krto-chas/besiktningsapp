"""
=============================================================================
BESIKTNINGSAPP BACKEND - CONFIGURATION
=============================================================================
Configuration management following 12-factor app principles.
All configuration via environment variables.
"""

import os
from datetime import timedelta
from typing import Any, Dict


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False
    ENV = "production"
    
    # Application
    VERSION = "1.0.0"
    API_VERSION = os.getenv("API_VERSION", "v1")
    API_BASE_PATH = os.getenv("API_BASE_PATH", "/api/v1")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        os.getenv("DATABASE_URL", "postgresql://besiktning:besiktning@localhost:5432/besiktningsapp")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000"))
    )
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    
    # CORS
    CORS_ENABLED = os.getenv("CORS_ENABLED", "true").lower() == "true"
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:19000,http://localhost:19006"
    ).split(",")
    CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = [
        "Content-Type",
        "Authorization",
        "X-Request-Id",
        "X-Idempotency-Key",
    ]
    
    # Storage
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # 'local' or 's3'
    
    # Local storage
    LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "/app/storage")
    LOCAL_STORAGE_IMAGES_PATH = os.getenv(
        "LOCAL_STORAGE_IMAGES_PATH",
        f"{LOCAL_STORAGE_PATH}/images"
    )
    LOCAL_STORAGE_PDFS_PATH = os.getenv(
        "LOCAL_STORAGE_PDFS_PATH",
        f"{LOCAL_STORAGE_PATH}/pdfs"
    )
    
    # S3/MinIO storage
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "besiktningsapp")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_USE_SSL = os.getenv("S3_USE_SSL", "false").lower() == "true"
    S3_PRESIGNED_URL_EXPIRATION = int(os.getenv("S3_PRESIGNED_URL_EXPIRATION", "3600"))
    
    # File upload limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(50 * 1024 * 1024)))  # 50MB
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    MAX_PDF_SIZE = int(os.getenv("MAX_PDF_SIZE", str(50 * 1024 * 1024)))  # 50MB
    
    ALLOWED_IMAGE_EXTENSIONS = set(
        os.getenv("ALLOWED_IMAGE_EXTENSIONS", "jpg,jpeg,png,webp").split(",")
    )
    ALLOWED_IMAGE_MIMETYPES = set(
        os.getenv("ALLOWED_IMAGE_MIMETYPES", "image/jpeg,image/png,image/webp").split(",")
    )
    
    # PDF Generation
    PDF_ENGINE = os.getenv("PDF_ENGINE", "reportlab")
    PDF_DPI = int(os.getenv("PDF_DPI", "300"))
    PDF_PAGE_SIZE = os.getenv("PDF_PAGE_SIZE", "A4")
    PDF_MARGIN_TOP = float(os.getenv("PDF_MARGIN_TOP", "2.0"))
    PDF_MARGIN_BOTTOM = float(os.getenv("PDF_MARGIN_BOTTOM", "2.0"))
    PDF_MARGIN_LEFT = float(os.getenv("PDF_MARGIN_LEFT", "2.0"))
    PDF_MARGIN_RIGHT = float(os.getenv("PDF_MARGIN_RIGHT", "2.0"))
    
    # Sync Configuration
    SYNC_CONFLICT_POLICY_DEFAULT = os.getenv("SYNC_CONFLICT_POLICY_DEFAULT", "LWW")
    SYNC_MIN_CLIENT_VERSION = os.getenv("SYNC_MIN_CLIENT_VERSION", "1.0.0")
    SYNC_IDEMPOTENCY_TTL = int(os.getenv("SYNC_IDEMPOTENCY_TTL", "86400"))  # 24 hours
    SYNC_MAX_BATCH_SIZE = int(os.getenv("SYNC_MAX_BATCH_SIZE", "100"))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
    RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "redis://localhost:6379/0")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Celery (task queue)
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # 'text' or 'json'
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/besiktningsapp/app.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Health Checks
    HEALTH_CHECK_DATABASE = os.getenv("HEALTH_CHECK_DATABASE", "true").lower() == "true"
    HEALTH_CHECK_STORAGE = os.getenv("HEALTH_CHECK_STORAGE", "true").lower() == "true"
    HEALTH_CHECK_REDIS = os.getenv("HEALTH_CHECK_REDIS", "false").lower() == "true"
    
    # Monitoring
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    
    PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
    
    # Timezone
    TIMEZONE = os.getenv("TZ", "Europe/Stockholm")
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with this config."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    ENV = "development"
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
    
    # Relaxed CORS for development
    CORS_ORIGINS = ["*"]
    
    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings."""
        Config.init_app(app)
        
        # Log configuration
        app.logger.info("Running in DEVELOPMENT mode")
        app.logger.debug("Debug mode: ENABLED")
        app.logger.debug(f"Database: {cls.SQLALCHEMY_DATABASE_URI[:50]}...")


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    ENV = "production"
    TESTING = False
    
    # Stricter settings in production
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Production must have proper secrets
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        Config.init_app(app)
        
        # Validate critical configuration
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production!")
        
        if cls.JWT_SECRET_KEY == cls.SECRET_KEY and cls.SECRET_KEY.startswith("dev-"):
            raise ValueError("JWT_SECRET_KEY must be set in production!")
        
        # Setup Sentry if configured
        if cls.SENTRY_DSN:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            
            sentry_sdk.init(
                dsn=cls.SENTRY_DSN,
                integrations=[FlaskIntegration()],
                environment=cls.SENTRY_ENVIRONMENT,
                traces_sample_rate=cls.SENTRY_TRACES_SAMPLE_RATE,
            )
            app.logger.info("Sentry monitoring enabled")
        
        app.logger.info("Running in PRODUCTION mode")


class TestingConfig(Config):
    """Testing configuration."""
    
    DEBUG = False
    ENV = "testing"
    TESTING = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )
    
    # Disable rate limiting in tests
    RATE_LIMIT_ENABLED = False
    
    # Use temporary directories for file storage
    LOCAL_STORAGE_PATH = "/tmp/besiktningsapp-test"
    LOCAL_STORAGE_IMAGES_PATH = "/tmp/besiktningsapp-test/images"
    LOCAL_STORAGE_PDFS_PATH = "/tmp/besiktningsapp-test/pdfs"
    
    # Fast JWT expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=300)  # 5 minutes
    
    @classmethod
    def init_app(cls, app):
        """Initialize testing-specific settings."""
        Config.init_app(app)
        app.logger.info("Running in TESTING mode")


# Configuration dictionary
config: Dict[str, Any] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str = "default") -> Config:
    """
    Get configuration class by name.
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configuration class
    """
    return config.get(config_name, config["default"])
