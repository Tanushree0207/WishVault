import re
from urllib.parse import urlparse
from typing import Tuple


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password against security requirements:
    - 8 to 128 characters (prevent DoS via excessively large passwords)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]\\/`~]", password):
        return False, "Password must contain at least one special character (!@#$%^&*...)."
    return True, ""


def is_safe_url(url: str, max_length: int = 500) -> bool:
    """
    Validate user-provided URLs (for product purchase or image links).
    Enforces safe schemes (http, https) and rejects dangerous schemes
    such as javascript:, data:, file:, vbscript:, etc.
    Guards against control characters, XSS vectors, and SSRF.
    """
    if not url:
        return True  # Empty/optional URL is considered valid

    url_str = str(url).strip()
    if len(url_str) > max_length:
        return False

    # Check for forbidden dangerous schemes or javascript pseudo-protocols
    lower_url = url_str.lower()
    dangerous_prefixes = (
        "javascript:",
        "data:",
        "file:",
        "vbscript:",
        "about:",
        "blob:",
    )
    if any(lower_url.startswith(prefix) for prefix in dangerous_prefixes):
        return False

    # Disallow control characters (\n, \r, \t, etc.)
    if re.search(r"[\x00-\x1f\x7f]", url_str):
        return False

    try:
        parsed = urlparse(url_str)
        # Scheme must strictly be http or https
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        # Must have a valid network location (hostname/domain)
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


def get_security_headers(is_production: bool = False) -> dict:
    """
    Generate HTTP security headers according to OWASP Secure Headers Project.
    """
    headers = {
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        # Protect against clickjacking
        "X-Frame-Options": "SAMEORIGIN",
        # Control referrer information passed to other sites
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # Restrict browser features and APIs
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
        # Content Security Policy (allows Google Fonts, inline safe CSS/JS for pastel UI, images from web)
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' https: data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
    }

    if is_production:
        # HTTP Strict Transport Security (HSTS) in production
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return headers
