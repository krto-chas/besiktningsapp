"""
=============================================================================
BESIKTNINGSAPP BACKEND - MAIN APPLICATION
=============================================================================
Flask application factory with endpoint registration and middleware setup.
"""

import logging
import os
from typing import Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from app.config import get_config
from app.extensions import (
    db,
    migrate,
    jwt,
    cors,
    limiter,
    init_extensions,
)


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Flask application factory.
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Setup logging
    setup_logging(app)
    
    return app


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.api.v1 import api_v1_bp
    
    # Register API v1 blueprint
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")
    
    # Health check endpoints (not versioned)
    @app.route("/health", methods=["GET"])
    @limiter.exempt
    def health_check():
        """Liveness probe - checks if app is running."""
        return jsonify({
            "status": "healthy",
            "service": "besiktningsapp-backend",
            "version": app.config.get("VERSION", "1.0.0")
        }), 200
    
    @app.route("/ready", methods=["GET"])
    @limiter.exempt
    def readiness_check():
        """Readiness probe - checks if app can handle requests."""
        checks = {
            "database": False,
            "storage": False,
        }
        
        # Check database
        try:
            db.session.execute(db.text("SELECT 1"))
            checks["database"] = True
        except Exception as e:
            app.logger.error(f"Database health check failed: {e}")
        
        # Check storage (if enabled)
        if app.config.get("HEALTH_CHECK_STORAGE", True):
            try:
                from app.services.storage_service import get_storage_service
                storage = get_storage_service()
                storage.health_check()
                checks["storage"] = True
            except Exception as e:
                app.logger.error(f"Storage health check failed: {e}")
        else:
            checks["storage"] = True  # Skip if disabled
        
        # All checks must pass
        all_healthy = all(checks.values())
        status_code = 200 if all_healthy else 503
        
        return jsonify({
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks
        }), status_code


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for standard HTTP errors and custom exceptions."""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """Handle HTTP exceptions."""
        response = {
            "error": {
                "code": error.name.lower().replace(" ", "_"),
                "message": error.description,
            }
        }
        return jsonify(response), error.code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({
            "error": {
                "code": "bad_request",
                "message": "Invalid request format or parameters",
            }
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized."""
        return jsonify({
            "error": {
                "code": "unauthorized",
                "message": "Authentication required",
            }
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden."""
        return jsonify({
            "error": {
                "code": "forbidden",
                "message": "Access denied",
            }
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found."""
        return jsonify({
            "error": {
                "code": "not_found",
                "message": "Resource not found",
            }
        }), 404
    
    @app.errorhandler(409)
    def handle_conflict(error):
        """Handle 409 Conflict."""
        return jsonify({
            "error": {
                "code": "conflict",
                "message": "Resource conflict",
            }
        }), 409
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle 422 Unprocessable Entity."""
        return jsonify({
            "error": {
                "code": "unprocessable_entity",
                "message": "Validation failed",
            }
        }), 422
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle 429 Too Many Requests."""
        return jsonify({
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests, please try again later",
            }
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "An internal error occurred",
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Handle unexpected errors."""
        app.logger.exception(f"Unexpected error: {error}")
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
            }
        }), 500


def register_middleware(app: Flask) -> None:
    """Register middleware for request/response processing."""
    
    @app.before_request
    def before_request():
        """Execute before each request."""
        # Log request
        request_id = request.headers.get("X-Request-Id", "N/A")
        app.logger.info(
            f"Request: {request.method} {request.path} "
            f"[Request-ID: {request_id}]"
        )
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Add request ID to response headers
        request_id = request.headers.get("X-Request-Id")
        if request_id:
            response.headers["X-Request-Id"] = request_id
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Log response
        app.logger.info(
            f"Response: {response.status_code} "
            f"[Request-ID: {request_id or 'N/A'}]"
        )
        
        return response


def register_cli_commands(app: Flask) -> None:
    """Register custom Flask CLI commands."""
    
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo("Database initialized.")
    
    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with initial data."""
        from app.models.standard_defect import StandardDefect
        from app.models.user import User
        import bcrypt
        
        # Create default admin user
        if not User.query.filter_by(email="admin@besiktningsapp.se").first():
            admin = User(
                email="admin@besiktningsapp.se",
                name="Administrator",
                password_hash=bcrypt.hashpw(
                    "admin123".encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8"),
                role="admin",
            )
            db.session.add(admin)
        
        # Create standard defects (templates)
        standard_defects = [
            {
                "code": "VF01",
                "title": "Från-luftsventil saknas",
                "description": "Från-luftsventil saknas i rum",
                "remedy": "Installera från-luftsventil enligt BBR",
                "severity": "high",
            },
            {
                "code": "VF02",
                "title": "Ventil defekt",
                "description": "Ventil är trasig eller fungerar ej",
                "remedy": "Byt ventil",
                "severity": "medium",
            },
            {
                "code": "VF03",
                "title": "För lågt flöde",
                "description": "Luftflödet understiger krav",
                "remedy": "Justera flöde eller byt aggregat",
                "severity": "medium",
            },
        ]
        
        for defect_data in standard_defects:
            if not StandardDefect.query.filter_by(code=defect_data["code"]).first():
                defect = StandardDefect(**defect_data)
                db.session.add(defect)
        
        db.session.commit()
        click.echo("Database seeded with initial data.")


def setup_logging(app: Flask) -> None:
    """Setup application logging."""
    log_level = app.config.get("LOG_LEVEL", "INFO")
    log_format = app.config.get("LOG_FORMAT", "text")
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if log_format == "text"
        else None,  # JSON format handled by python-json-logger if needed
    )
    
    # Set Flask logger level
    app.logger.setLevel(getattr(logging, log_level))
    
    # Log startup info
    app.logger.info(f"Starting Besiktningsapp Backend API (ENV: {app.config['ENV']})")
    app.logger.info(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50]}...")
    app.logger.info(f"Storage Backend: {app.config.get('STORAGE_BACKEND', 'local')}")


# Import click for CLI commands
import click


# Create default app instance for CLI
def cli():
    """CLI entry point."""
    app = create_app()
    return app


if __name__ == "__main__":
    # For development only
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
