"""
=============================================================================
BESIKTNINGSAPP BACKEND - LOGGER
=============================================================================
Logging configuration and utilities.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

from flask import Flask, has_request_context, request


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request info."""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.remote_addr = request.remote_addr
            record.request_id = request.headers.get('X-Request-Id', 'N/A')
        else:
            record.url = None
            record.method = None
            record.remote_addr = None
            record.request_id = None
        
        return super().format(record)


def setup_logging(app: Flask):
    """
    Setup logging configuration.
    
    Args:
        app: Flask application
    """
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', 'text')
    
    # Create formatter
    if log_format == 'json':
        # TODO: Use python-json-logger for structured logging
        formatter = RequestFormatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
            '"message": "%(message)s", "request_id": "%(request_id)s"}'
        )
    else:
        formatter = RequestFormatter(
            '[%(asctime)s] %(levelname)s in %(module)s [%(request_id)s]: %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # File handler (if configured)
    log_file = app.config.get('LOG_FILE')
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
    
    # Add console handler
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Set werkzeug logger level
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
