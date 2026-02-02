"""
=============================================================================
BESIKTNINGSAPP BACKEND - EXTENSIONS
=============================================================================
Flask extensions initialization.
Extensions are initialized here and bound to the app in the factory.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# =============================================================================
# EXTENSIONS INSTANCES
# =============================================================================

# Database (SQLAlchemy 2.x)
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# JWT authentication
jwt = JWTManager()

# CORS
cors = CORS()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],
    storage_uri="redis://localhost:6379/0",
)


# =============================================================================
# EXTENSION INITIALIZATION
# =============================================================================

def init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions with app instance.
    
    Args:
        app: Flask application instance
    """
    # SQLAlchemy
    db.init_app(app)
    
    # Migrate
    migrate.init_app(app, db)
    
    # JWT
    jwt.init_app(app)
    _configure_jwt(app)
    
    # CORS
    if app.config.get("CORS_ENABLED", True):
        cors.init_app(
            app,
            origins=app.config.get("CORS_ORIGINS", ["*"]),
            methods=app.config.get("CORS_METHODS", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]),
            allow_headers=app.config.get("CORS_ALLOW_HEADERS", ["Content-Type", "Authorization"]),
            supports_credentials=app.config.get("CORS_ALLOW_CREDENTIALS", True),
        )
    
    # Rate Limiter
    if app.config.get("RATE_LIMIT_ENABLED", True):
        limiter.init_app(app)
        limiter.storage_uri = app.config.get("RATE_LIMIT_STORAGE_URL", "redis://localhost:6379/0")
    
    app.logger.info("Extensions initialized successfully")


def _configure_jwt(app: Flask) -> None:
    """
    Configure JWT extension with custom handlers.
    
    Args:
        app: Flask application instance
    """
    from flask import jsonify
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token."""
        return jsonify({
            "error": {
                "code": "token_expired",
                "message": "The token has expired",
            }
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token."""
        return jsonify({
            "error": {
                "code": "invalid_token",
                "message": "Invalid token format",
            }
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token."""
        return jsonify({
            "error": {
                "code": "token_missing",
                "message": "Authorization token is required",
            }
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked token."""
        return jsonify({
            "error": {
                "code": "token_revoked",
                "message": "The token has been revoked",
            }
        }), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        """Handle token verification failure."""
        return jsonify({
            "error": {
                "code": "token_verification_failed",
                "message": "Token verification failed",
            }
        }), 401
