"""
NEXUS AI - JWT Authentication & Role-Based Access Control (RBAC) Module
Provides token creation, decoding, and route protection decorators.
"""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
from flask import jsonify, request

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "nexus-ai-enterprise-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_jwt_token(user: Dict[str, Any]) -> str:
    """Generate a signed JWT token containing user identity and role."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_authenticated_user() -> Optional[Dict[str, Any]]:
    """Extract authenticated user from Authorization header if present."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        return decode_jwt_token(token)
    return None


def jwt_required(optional: bool = False):
    """Decorator to enforce valid JWT token on protected routes."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_authenticated_user()
            if not user and not optional:
                return jsonify({"error": "Unauthorized. Valid Bearer JWT token required."}), 401
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def roles_required(*allowed_roles: str):
    """Decorator to enforce specific roles (e.g., 'agent', 'admin')."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_authenticated_user()
            if not user:
                return jsonify({"error": "Authentication required."}), 401
            if user.get("role") not in allowed_roles:
                return jsonify({
                    "error": f"Forbidden. Role '{user.get('role')}' does not have permission. Allowed: {list(allowed_roles)}"
                }), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
