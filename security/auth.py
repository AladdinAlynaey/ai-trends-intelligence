"""
Authentication & authorization: JWT tokens, password hashing, decorators.
"""
import functools
import time
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from flask import request, jsonify, g, current_app

from data.store import (
    read_json, write_json, find_item, append_item,
    generate_id, utcnow, append_audit_log
)


# ── Password Hashing ──────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── JWT Token Management ──────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    cfg = current_app.config
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + cfg.get(
            "JWT_ACCESS_EXPIRES", timedelta(hours=1)
        ),
        "jti": generate_id(),
    }
    return jwt.encode(payload, cfg["JWT_SECRET_KEY"], algorithm="HS256")


def create_refresh_token(user_id: str, role: str) -> str:
    cfg = current_app.config
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + cfg.get(
            "JWT_REFRESH_EXPIRES", timedelta(days=7)
        ),
        "jti": generate_id(),
    }
    token = jwt.encode(payload, cfg["JWT_SECRET_KEY"], algorithm="HS256")
    # Store refresh token for rotation / revocation
    tokens_file = cfg.get("TOKENS_FILE", "data/tokens.json")
    tokens = read_json(tokens_file, [])
    tokens.append({
        "jti": payload["jti"],
        "user_id": user_id,
        "created_at": utcnow(),
        "revoked": False,
    })
    write_json(tokens_file, tokens)
    return token


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def revoke_token(jti: str) -> None:
    tokens_file = current_app.config.get("TOKENS_FILE", "data/tokens.json")
    tokens = read_json(tokens_file, [])
    for t in tokens:
        if t.get("jti") == jti:
            t["revoked"] = True
    write_json(tokens_file, tokens)


def is_token_revoked(jti: str) -> bool:
    tokens_file = current_app.config.get("TOKENS_FILE", "data/tokens.json")
    tokens = read_json(tokens_file, [])
    for t in tokens:
        if t.get("jti") == jti:
            return t.get("revoked", False)
    return False


# ── Decorators ─────────────────────────────────────

def login_required(f):
    """Require a valid JWT access token."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "Invalid token type"}), 401
        if is_token_revoked(payload.get("jti", "")):
            return jsonify({"error": "Token has been revoked"}), 401

        g.current_user_id = payload["sub"]
        g.current_user_role = payload.get("role", "user")
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Require admin role."""
    @functools.wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if g.current_user_role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


# ── CSRF Token Helpers ─────────────────────────────

def generate_csrf_token() -> str:
    return generate_id() + generate_id()


def validate_csrf(token: str) -> bool:
    """Validate CSRF token from request headers."""
    expected = request.headers.get("X-CSRF-Token", "")
    return token == expected and len(token) > 30
