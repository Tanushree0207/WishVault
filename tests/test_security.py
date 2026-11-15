from app import create_app
from app.models.user import User


def test_csrf_protection_rejects_missing_token():
    """Security Test: Verify Flask-WTF rejects POST requests without valid CSRF token."""
    csrf_app = create_app("testing")
    csrf_app.config["WTF_CSRF_ENABLED"] = True
    csrf_client = csrf_app.test_client()

    # Attempt POST request without CSRF token
    res = csrf_client.post(
        "/auth/login",
        data={"email": "attacker@example.com", "password": "Password123!"},
    )
    # Must reject with 400 Bad Request
    assert res.status_code == 400
    assert b"CSRF" in res.data or b"Bad Request" in res.data or b"Invalid request" in res.data


def test_rate_limiting_on_auth_endpoint(app):
    """Security Test: Verify Flask-Limiter enforces rate limits on login endpoint."""
    from app.extensions import limiter

    original_enabled = limiter.enabled
    original_config = app.config.get("RATELIMIT_ENABLED", False)

    try:
        app.config["RATELIMIT_ENABLED"] = True
        limiter.enabled = True
        limiter.init_app(app)

        limit_client = app.test_client()
        responses = []
        for _ in range(7):
            res = limit_client.post(
                "/auth/login",
                data={"email": "rate_test@wishvault.io", "password": "WrongPassword1!"},
            )
            responses.append(res.status_code)

        # The auth limit is 5 per minute: the 6th login attempt returns HTTP 429
        assert responses[5] == 429
        assert 429 in responses
    finally:
        limiter.enabled = original_enabled
        app.config["RATELIMIT_ENABLED"] = original_config


def test_sql_injection_resistance(app, auth_client_a, user_a):
    """Security Test: Verify SQL injection payloads in search query are safely parameterized."""
    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE products; --",
        "1 UNION SELECT 1, 2, 3, 4, 5, 6, 7, 8, 9, 10--",
        "' OR 1=1 --",
    ]

    for payload in sql_payloads:
        res = auth_client_a.get(f"/products/?q={payload}")
        # The app must return 200 without executing the injected SQL or raising database syntax errors
        assert res.status_code == 200
        # Verify the database tables were not dropped or corrupted
        with app.app_context():
            assert User.query.count() >= 1


def test_security_headers_present(client):
    """Security Test: Verify OWASP security headers in HTTP response."""
    res = client.get("/")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "Content-Security-Policy" in res.headers
    assert "default-src 'self'" in res.headers["Content-Security-Policy"]
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_custom_error_pages_no_leakage(client):
    """Security Test: Ensure 404 and 403 error responses do not leak server stack traces."""
    res_404 = client.get("/this-route-does-not-exist")
    assert res_404.status_code == 404
    assert b"Page Not Found" in res_404.data
    assert b"Traceback (most recent call last)" not in res_404.data

    res_403 = client.get("/products/9999999")
    # Nonexistent product redirects or 404s
    assert res_403.status_code in (404, 302)
