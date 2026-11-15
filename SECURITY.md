# WishVault Security Architecture & Implementation Guide

> **Secure Software Engineering Academic Project Documentation**

WishVault was architected and built with **Security by Design** principles. Rather than adding security controls as an afterthought or patch, defensive mechanisms were incorporated into every tier: database models, ORM queries, authentication workflows, session management, input validation, HTTP response headers, and automated test suites.

---

## Threat Model & Security Controls Matrix

| Threat Category | Potential Attack Vector | WishVault Security Control | Verification Test |
| :--- | :--- | :--- | :--- |
| **A. Broken Authentication** | Credential stuffing, brute-force attacks, plaintext password leakage | Werkzeug `scrypt` hashing, constant-time verification, password complexity enforcement (min 8 chars, mixed case, numbers, symbols), session fixation protection, rate limiting (5 attempts/min). | `test_auth.py`, `test_security.py` |
| **B. Broken Access Control (IDOR)** | Horizontal privilege escalation: User A accessing or modifying User B's products, collections, purchases, or budgets | Multi-tenant user isolation enforced on the backend. Every query, mutation, and delete operation validates `owner_id == current_user.id` or queries strictly by `current_user.id`. Unauthorized attempts return `HTTP 403 Forbidden`. | `test_authorization.py` (7 tests) |
| **C. Injection (SQLi)** | Attacker injecting SQL via search fields, sorting, or filtering parameters | 100% parameterized queries via SQLAlchemy 2.0 ORM. Bound parameters for all ILIKE searches. Zero raw string concatenation in SQL queries. SQLite foreign key enforcement enabled via connection PRAGMAs. | `test_security.py::test_sql_injection_resistance` |
| **D. Cross-Site Request Forgery (CSRF)** | Malicious third-party site submitting unauthorized state changes on behalf of a logged-in user | Flask-WTF `CSRFProtect` active across all HTTP POST forms and asynchronous requests via `<meta name="csrf-token">` and form tokens. 1-hour time-limited tokens. Invalid or missing tokens rejected with `HTTP 400 Bad Request`. | `test_security.py::test_csrf_protection_rejects_missing_token` |
| **E. Cross-Site Scripting (XSS)** | Injection of `javascript:` or `data:` payloads in product links, image URLs, or input fields | Strict server-side URL validation (`is_safe_url`) accepting only safe schemes (`http://` and `https://`), control character stripping, reverse tabnabbing defense (`rel="noopener noreferrer"`), and automatic Jinja2 context-aware HTML escaping. | `test_products.py::test_dangerous_url_schemes_rejected` |
| **F. Denial of Service (DoS) & Brute Force** | Rapid authentication requests, hashing CPU exhaustion | Flask-Limiter applied to `/auth/login`, `/auth/register`, and `/auth/forgot-password` (5/min). Maximum input length constraints on all string and password fields (max 128 chars for passwords). | `test_security.py::test_rate_limiting_on_auth_endpoint` |
| **G. Security Misconfiguration & Info Leakage** | Database stack traces exposed in 404/500 errors, clickjacking, MIME sniffing | Custom error handlers for 400, 403, 404, 429, and 500 returning safe user-facing pages without stack traces. OWASP-aligned response headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`. | `test_security.py::test_security_headers_present`, `test_custom_error_pages_no_leakage` |
| **H. Insecure Sessions** | Session hijacking, cookie theft | `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, configurable `SESSION_COOKIE_SECURE = True` in production over HTTPS. Session rotation via `session.clear()` upon login and logout. | `test_auth.py::test_logout`, `test_auth.py::test_unauthorized_access_prevention` |

---

## Detailed Control Implementations

### 1. Password Security & Hashing
- **Algorithm**: Passwords are hashed using Werkzeug's `generate_password_hash` (`scrypt` / `pbkdf2:sha256`) with unique per-user cryptographic salts.
- **Plaintext Policy**: Plaintext passwords are never stored in the database, never returned in API payloads, and never printed to application logs.
- **Complexity Requirements**:
  - Minimum 8 characters, maximum 128 characters (prevents CPU exhaustion attacks).
  - At least one uppercase letter `[A-Z]`.
  - At least one lowercase letter `[a-z]`.
  - At least one digit `[0-9]`.
  - At least one special symbol `[!@#$%^&*...]`.

### 2. IDOR Prevention & Multi-Tenant Authorization
Every product, collection, purchase, and monthly budget is strictly bound to its creator's `user_id`:
- **Read Operations**: Filtered using `filter_by(user_id=current_user.id)`.
- **Direct Resource Lookups**: When accessed by ID (e.g. `/products/<id>`, `/collections/<id>`), backend logic explicitly executes:
  ```python
  product = Product.query.get_or_404(product_id)
  if product.user_id != current_user.id:
      abort(403)
  ```
- **State Changes**: Deletion, editing, marking as purchased, and undoing purchases strictly verify ownership before modifying database state.

### 3. Server-Side Input Validation
All user-submitted parameters pass through WTForms validators and specialized sanitization functions before reaching the ORM:
- **Price Validation**: Must be positive and realistic (min `0.01`, max `10,000,000.00` INR). Negative numbers, zero, and non-numeric inputs are rejected.
- **Budget Validation**: Monthly budgets must be `>= 0.00`.
- **URL Sanitization (`is_safe_url`)**:
  - Rejects dangerous schemes (`javascript:`, `data:`, `file:`, `vbscript:`).
  - Only allows `http://` and `https://` with valid network locations.
  - Rejects ASCII control characters (`\x00-\x1f`).
  - **No Server-Side URL Fetching**: The server never makes HTTP requests to user-provided URLs, completely mitigating Server-Side Request Forgery (SSRF).

### 4. Token-Based Password Reset
- Reset tokens are generated using `itsdangerous.URLSafeTimedSerializer` with a dedicated salt (`password-reset-salt`).
- Tokens expire automatically after 1 hour (3600 seconds).
- Tokens cannot be replayed or forged without the application's `SECRET_KEY`.
- Invalid or expired tokens gracefully redirect to the forgot password screen with security warnings.

### 5. HTTP Security Headers
Every HTTP response carries protective headers injected via `@app.after_request`:
```http
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' https: data:; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self';
```

### 6. SQLite Relational Integrity
SQLite does not enforce foreign keys by default. WishVault attaches an event listener to the SQLAlchemy connection engine:
```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```
Cascading deletes (`ON DELETE CASCADE`) are defined on child records (`Product`, `Collection`, `Purchase`, `Budget`) so orphaned records are prevented when an account is deleted.

---

## Security Verification & Auditing
To execute the automated security verification suite:
```bash
.venv/bin/pytest tests/test_security.py tests/test_authorization.py -v
```
All tests verify access control, CSRF rejection, rate limiting, and SQL injection resistance at the backend level.
