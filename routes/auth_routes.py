"""
Authentication routes — register, login, refresh, logout.
"""
from flask import Blueprint, request, jsonify
from security.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, revoke_token, login_required,
)
from security.validation import (
    validate_email, validate_username, validate_password, sanitize_html,
)
from data.store import (
    find_item, append_item, read_json, append_audit_log,
)
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = sanitize_html(data.get("username", "").strip())
    email = sanitize_html(data.get("email", "").strip().lower())
    password = data.get("password", "")

    # Validate
    if not validate_username(username):
        return jsonify({"error": "Invalid username (3-30 chars, alphanumeric/_/-)"}), 400
    if not validate_email(email):
        return jsonify({"error": "Invalid email address"}), 400
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"error": msg}), 400

    # Check duplicates
    if find_item(Config.USERS_FILE, "username", username):
        return jsonify({"error": "Username already exists"}), 409
    if find_item(Config.USERS_FILE, "email", email):
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    user = append_item(Config.USERS_FILE, {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": "user",
        "active": True,
        "preferences": {
            "feeds": [],
            "platforms": [],
        },
    })

    append_audit_log(Config.AUDIT_LOG_DIR, "user_registered",
                     user_id=user["id"], ip=request.remote_addr)

    return jsonify({
        "message": "Registration successful",
        "user": {"id": user["id"], "username": username, "role": "user"},
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    login_id = sanitize_html(data.get("username", "").strip())
    password = data.get("password", "")

    if not login_id or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Find by username or email
    user = find_item(Config.USERS_FILE, "username", login_id)
    if not user:
        user = find_item(Config.USERS_FILE, "email", login_id.lower())
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.get("active", True):
        return jsonify({"error": "Account is deactivated"}), 403

    if not verify_password(password, user.get("password_hash", "")):
        append_audit_log(Config.AUDIT_LOG_DIR, "login_failed",
                         user_id=user["id"], ip=request.remote_addr)
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(user["id"], user.get("role", "user"))
    refresh_token = create_refresh_token(user["id"], user.get("role", "user"))

    append_audit_log(Config.AUDIT_LOG_DIR, "login_success",
                     user_id=user["id"], ip=request.remote_addr)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", "user"),
        },
    })


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return jsonify({"error": "Invalid refresh token"}), 401

    # Rotate: revoke old, issue new
    revoke_token(payload.get("jti", ""))

    new_access = create_access_token(payload["sub"], payload.get("role", "user"))
    new_refresh = create_refresh_token(payload["sub"], payload.get("role", "user"))

    return jsonify({
        "access_token": new_access,
        "refresh_token": new_refresh,
    })


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1] if " " in auth_header else ""
    payload = decode_token(token)
    if payload:
        revoke_token(payload.get("jti", ""))

    from flask import g
    append_audit_log(Config.AUDIT_LOG_DIR, "logout",
                     user_id=g.current_user_id, ip=request.remote_addr)

    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    from flask import g
    user = find_item(Config.USERS_FILE, "id", g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "display_name": user.get("display_name", user["username"]),
        "preferences": user.get("preferences", {}),
        "created_at": user.get("created_at"),
    })


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change password for the current user."""
    from flask import g
    data = request.get_json(silent=True) or {}
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if not current_pw or not new_pw:
        return jsonify({"error": "Current and new passwords required"}), 400

    valid, msg = validate_password(new_pw)
    if not valid:
        return jsonify({"error": msg}), 400

    user = find_item(Config.USERS_FILE, "id", g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not verify_password(current_pw, user.get("password_hash", "")):
        return jsonify({"error": "Current password is incorrect"}), 401

    # Update password
    from data.store import update_item
    update_item(Config.USERS_FILE, g.current_user_id, {
        "password_hash": hash_password(new_pw),
    })

    append_audit_log(Config.AUDIT_LOG_DIR, "password_changed",
                     user_id=g.current_user_id, ip=request.remote_addr)

    return jsonify({"message": "Password changed successfully"})


@auth_bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    """Update profile information."""
    from flask import g
    data = request.get_json(silent=True) or {}
    email = sanitize_html(data.get("email", "").strip().lower())
    display_name = sanitize_html(data.get("display_name", "").strip())

    updates = {}
    if email and validate_email(email):
        # Check for duplicate
        existing = find_item(Config.USERS_FILE, "email", email)
        if existing and existing.get("id") != g.current_user_id:
            return jsonify({"error": "Email already in use"}), 409
        updates["email"] = email

    if display_name:
        updates["display_name"] = display_name

    if updates:
        from data.store import update_item
        update_item(Config.USERS_FILE, g.current_user_id, updates)

    return jsonify({"message": "Profile updated"})



@auth_bp.route("/save-keys", methods=["POST"])
@login_required
def save_api_keys():
    """Save API keys to the .env file (admin only or self)."""
    from flask import g
    import os, re

    data = request.get_json(silent=True) or {}

    env_path = os.path.join(Config.BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return jsonify({"error": ".env file not found"}), 500

    def _upsert(content, key, value):
        """Update existing key or append if missing."""
        if not value:
            return content
        pattern = rf"^{re.escape(key)}=.*$"
        if re.search(pattern, content, flags=re.MULTILINE):
            return re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
        else:
            return content.rstrip("\n") + f"\n{key}={value}\n"

    try:
        with open(env_path, "r") as f:
            content = f.read()

        # Core keys
        content = _upsert(content, "OPENROUTER_API_KEY", data.get("openrouter_api_key", "").strip())
        content = _upsert(content, "TELEGRAM_BOT_TOKEN", data.get("telegram_bot_token", "").strip())
        content = _upsert(content, "TELEGRAM_ADMIN_CHAT_ID", data.get("telegram_admin_chat_id", "").strip())
        content = _upsert(content, "OPENROUTER_LLM_MODEL", data.get("llm_model", "").strip())
        content = _upsert(content, "OPENROUTER_IMAGE_MODEL", data.get("image_model", "").strip())

        # Telegram enabled
        tg_enabled = data.get("telegram_enabled")
        if tg_enabled is not None:
            content = _upsert(content, "TELEGRAM_ENABLED", "true" if tg_enabled else "false")

        # Twitter/X
        content = _upsert(content, "TWITTER_API_KEY", data.get("twitter_api_key", "").strip())
        content = _upsert(content, "TWITTER_API_SECRET", data.get("twitter_api_secret", "").strip())
        content = _upsert(content, "TWITTER_ACCESS_TOKEN", data.get("twitter_access_token", "").strip())
        content = _upsert(content, "TWITTER_ACCESS_SECRET", data.get("twitter_access_secret", "").strip())

        # LinkedIn
        content = _upsert(content, "LINKEDIN_ACCESS_TOKEN", data.get("linkedin_access_token", "").strip())

        # Krea.ai
        content = _upsert(content, "KREA_API_KEY", data.get("krea_api_key", "").strip())

        with open(env_path, "w") as f:
            f.write(content)

        append_audit_log(Config.AUDIT_LOG_DIR, "api_keys_updated",
                         user_id=g.current_user_id,
                         details="API keys updated via settings",
                         ip=request.remote_addr)

        return jsonify({"message": "API keys saved. Restart the app for changes to take effect."})
    except Exception as e:
        return jsonify({"error": f"Failed to save keys: {str(e)}"}), 500
