"""
Input validation and sanitization utilities.
"""
import re
import bleach


def sanitize_html(text: str) -> str:
    """Strip all HTML tags."""
    return bleach.clean(text, tags=[], strip=True)


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email)) and len(email) <= 254


def validate_username(username: str) -> bool:
    pattern = r"^[a-zA-Z0-9_\-]{3,30}$"
    return bool(re.match(pattern, username))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength. Returns (is_valid, message)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "OK"


def validate_url(url: str) -> bool:
    pattern = r"^https?://[^\s<>\"']{3,2000}$"
    return bool(re.match(pattern, url))


def sanitize_search_query(query: str) -> str:
    """Sanitize a search query string."""
    query = sanitize_html(query)
    query = re.sub(r"[^\w\s\-.,?!@#&()'\"/]", "", query)
    return query[:500].strip()


def validate_trend_score(score) -> bool:
    try:
        s = int(score)
        return 0 <= s <= 100
    except (ValueError, TypeError):
        return False
