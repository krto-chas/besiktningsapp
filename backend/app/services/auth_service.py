"""
=============================================================================
BESIKTNINGSAPP BACKEND - AUTH SERVICE
=============================================================================
Authentication service for JWT token generation and validation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from jwt.exceptions import InvalidTokenError

from app.models import User
from app.extensions import db


class AuthService:
    """Authentication service for JWT operations."""
    
    @staticmethod
    def create_token(user_id: int, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user_id: User ID to encode in token
            additional_claims: Optional additional claims to include
            
        Returns:
            JWT token string
        """
        identity = user_id
        
        # Add additional claims if provided
        if additional_claims:
            return create_access_token(
                identity=identity,
                additional_claims=additional_claims
            )
        
        return create_access_token(identity=identity)
    
    @staticmethod
    def validate_token(token: str) -> Optional[int]:
        """
        Validate JWT token and extract user ID.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID if valid, None otherwise
        """
        try:
            decoded = decode_token(token)
            return decoded.get("sub")  # 'sub' contains the identity (user_id)
        except InvalidTokenError:
            return None
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            return None
        
        if not user.check_password(password):
            return None
        
        if not user.active:
            return None
        
        return user
    
    @staticmethod
    def get_token_expiration() -> int:
        """
        Get token expiration time in seconds.
        
        Returns:
            Expiration time in seconds
        """
        expires_delta = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
        if isinstance(expires_delta, timedelta):
            return int(expires_delta.total_seconds())
        return 3600  # Default 1 hour
    
    @staticmethod
    def refresh_user_token(user_id: int) -> Optional[str]:
        """
        Refresh token for user (verify user still exists and is active).
        
        Args:
            user_id: User ID
            
        Returns:
            New token if user is valid, None otherwise
        """
        user = User.query.get(user_id)
        
        if not user or not user.active:
            return None
        
        return AuthService.create_token(user_id)
    
    @staticmethod
    def create_user(
        email: str,
        password: str,
        name: str,
        role: str = "inspector"
    ) -> User:
        """
        Create new user (for admin/setup purposes).
        
        Args:
            email: User email
            password: Plain text password (will be hashed)
            name: Full name
            role: User role (default: inspector)
            
        Returns:
            Created User object
        """
        user = User(
            email=email.lower(),
            name=name,
            role=role,
            active=True
        )
        
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def update_user_password(user_id: int, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New password (plain text, will be hashed)
            
        Returns:
            True if successful, False otherwise
        """
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        user.set_password(new_password)
        db.session.commit()
        
        return True
    
    @staticmethod
    def verify_current_password(user_id: int, password: str) -> bool:
        """
        Verify user's current password.
        
        Args:
            user_id: User ID
            password: Password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        return user.check_password(password)
