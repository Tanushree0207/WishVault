# WishVault – Personal Shopping & Wishlist Manager

> **"Your wishes, beautifully organized."**
>
> *A Secure Software Engineering Academic Project*

WishVault is a complete, full-stack personal shopping and wishlist management web application built from scratch with Python Flask, SQLAlchemy, SQLite, and vanilla HTML5/CSS3/JavaScript. It combines a refined, boutique soft pastel lifestyle design aesthetic with rigorous application security controls engineered directly into its architecture from day one.

---

## 1. Features Overview

### 💖 Wishlist Management (My Wishlist)
- **Product Curation**: Save dream items with title, price in INR (₹), collection category, notes, and store links.
- **Image Fallback System**: Optional image URLs are treated as untrusted input. If an image fails to load or is unavailable, the UI gracefully renders an aesthetic pastel illustration fallback.
- **Search, Filter & Sort**: Real-time search by keyword, filter by collection or purchase status (active vs. fulfilled), and sort by price or date added.
- **Product Details View**: View full product specs, direct store links with reverse tabnabbing defense (`rel="noopener noreferrer"`), and purchase timestamps.

### 🗂️ Collections & Categories
- **Standard Default Collections**: Every new user starts with 7 curated lifestyle categories: *Fashion*, *Electronics*, *Beauty*, *Books*, *Accessories*, *Home & Living*, and *Other*.
- **Custom Collections**: Create bespoke categories with custom pastel colors and aesthetic icons.
- **Safe Cascade Deletion**: Deleting a custom collection safely unlinks its products to *Uncategorized* rather than deleting your saved items.

### 🛍️ Shopping Tracker
- **Fulfill Wishes**: Mark any wishlist product as purchased with the actual price paid, purchase date, and optional receipt/order notes.
- **Accidental Purchase Undo**: Easily revert a purchase back to the active wishlist with one click. Spending metrics and monthly budgets update instantly in real time.
- **Purchase History**: Complete log of all fulfilled items, total expenditure, and average item cost.

### 💰 Budget Manager
- **Monthly Spending Limits**: Set and adjust shopping budgets in INR for any month and year.
- **Real-Time Calculation**: Spending metrics are computed directly from actual database purchase records, never dummy numbers.
- **80% Threshold Warning**: An automated warning banner alerts users as soon as spending hits 80% of their monthly allocation.
- **Budget Exceeded Alert**: High-visibility alert when expenditure exceeds the set budget.
- **Visual Progress & Analytics**: Utilization meters and interactive 6-month historical trend charts powered by Chart.js.

### 🌸 Refined Pastel Design System
- **Startup Lifestyle Aesthetic**: Soft lavender (`#8B5CF6`) and blush pink (`#EC4899`) primary tones, soft peach accents, and warm off-white surfaces (`#FAF8FD`).
- **Modern Typography**: Clear readability using Google Font *Plus Jakarta Sans*.
- **Fully Responsive**: Mobile-friendly navigation drawer, collapsible sidebar, and adaptive CSS grid layouts across desktop, tablet, and mobile.
- **Native HTML5 Dialogs**: Accessible `<dialog>` modal components with backdrop blur and light-dismiss outside click handling.

---

## 2. Technology Stack

- **Backend Framework**: Python 3 (Flask 3.1)
- **Database & ORM**: SQLite 3 with SQLAlchemy 2.0 (Flask-SQLAlchemy)
- **Relational Integrity**: SQLite foreign key enforcement enabled via connection PRAGMAs (`PRAGMA foreign_keys=ON`)
- **Authentication**: Flask-Login with session fixation defense and strong session verification
- **Password Hashing**: Werkzeug security utilities (`scrypt` / `pbkdf2:sha256`)
- **CSRF Protection**: Flask-WTF `CSRFProtect` across all forms and asynchronous actions
- **Rate Limiting**: Flask-Limiter with endpoint-specific thresholds
- **Form & Input Validation**: WTForms with email validation and custom URL sanitization
- **Frontend**: Semantic HTML5, Modern CSS3 with CSS variables, Vanilla JavaScript (zero heavy JS framework bloat)
- **Data Visualization**: Chart.js (CSP-compliant via CDN)
- **Testing**: Pytest with automated unit, integration, authorization (IDOR), and security suites

---

## 3. Database Design

```
+---------------------------------------------------------------------------------+
|                                    USERS                                        |
+---------------------------------------------------------------------------------+
| id (PK) | full_name | email (UQ) | password_hash | created_at | updated_at      |
+---------------------------------------------------------------------------------+
       | 1                           | 1                          | 1
       |                             |                            |
       | N (Cascade)                 | N (Cascade)                | N (Cascade)
       v                             v                            v
+-----------------------+     +-----------------------+    +----------------------+
|      COLLECTIONS      |     |       PRODUCTS        |    |       BUDGETS        |
+-----------------------+     +-----------------------+    +----------------------+
| id (PK)               |     | id (PK)               |    | id (PK)              |
| user_id (FK -> users) |<----+ user_id (FK -> users) |    | user_id (FK -> users)|
| name                  |  N  | collection_id (FK)    |    | year                 |
| description           |     | name                  |    | month (1-12)         |
| icon, color           |     | price (INR)           |    | monthly_budget (INR) |
| is_default            |     | image_url, store_url  |    | created_at           |
| created_at            |     | is_purchased (Bool)   |    +----------------------+
+-----------------------+     | created_at            |    UQ: (user_id, yr, mon)
                              +-----------------------+
                                         | 1
                                         |
                                         | 1 (Cascade)
                                         v
                              +-----------------------+
                              |       PURCHASES       |
                              +-----------------------+
                              | id (PK)               |
                              | user_id (FK -> users) |
                              | product_id (FK -> UQ) |
                              | purchase_date         |
                              | actual_amount (INR)   |
                              | notes, created_at     |
                              +-----------------------+
```

### Relational Constraints
- **Multi-Tenant Ownership**: Foreign keys link every resource directly to its owning user.
- **Cascades**: Deleting a user account cascades to all associated products, collections, purchases, and budgets.
- **Collection Unlinking**: Deleting a collection sets `collection_id = NULL` on member products (`ON DELETE SET NULL`), preserving the product in the user's wishlist under *Uncategorized*.
- **One-to-One Purchase Constraint**: `Purchase.product_id` is unique, guaranteeing each product has exactly one purchase audit record.

---

## 4. Security Mechanisms Implemented

For complete security specifications, please refer to [`SECURITY.md`](SECURITY.md). Key mechanisms include:

1. **Password Security**:
   - Hashed using Werkzeug `scrypt` with unique per-user cryptographic salts.
   - Enforced complexity: minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special symbol.
   - Plaintext passwords and hashes are never exposed in API responses or log files.
2. **Horizontal Access Control (IDOR Prevention)**:
   - Backend verification on every operation (`product.user_id == current_user.id`).
   - Unauthorized attempts by User A to view, edit, delete, or mark User B's resources are rejected with `HTTP 403 Forbidden`.
3. **SQL Injection Defense**:
   - 100% parameterized queries via SQLAlchemy 2.0 ORM.
   - Search strings are escaped and bound as parameters in SQL `ILIKE` clauses.
4. **CSRF Protection**:
   - Flask-WTF `CSRFProtect` validates tokens on all POST requests.
   - Requests with missing or forged CSRF tokens are rejected with `HTTP 400 Bad Request`.
5. **Input & URL Sanitization**:
   - Prices and budgets must be strictly positive numeric values.
   - User-supplied URLs are inspected with `is_safe_url()`, disallowing dangerous schemes (`javascript:`, `data:`, `file:`) and control characters.
   - Server never fetches user URLs remotely, eliminating SSRF vectors.
6. **Rate Limiting**:
   - Flask-Limiter enforces 5 requests/minute on `/auth/login`, `/auth/register`, and `/auth/forgot-password`.
   - Returns `HTTP 429 Too Many Requests` when breached.
7. **Session Hardening**:
   - `SESSION_COOKIE_HTTPONLY = True` (prevents JavaScript cookie access).
   - `SESSION_COOKIE_SAMESITE = 'Lax'` (mitigates CSRF via top-level navigations).
   - `session.clear()` invoked upon login to prevent session fixation.
8. **OWASP HTTP Security Headers**:
   - `Content-Security-Policy`: Restricts scripts, fonts, and inline execution.
   - `X-Content-Type-Options: nosniff`: Prevents MIME type sniffing.
   - `X-Frame-Options: SAMEORIGIN`: Prevents clickjacking.
   - `Referrer-Policy: strict-origin-when-cross-origin`: Controls referrer leakage.
9. **Safe Error Handling**:
   - Custom templates for 400, 403, 404, 429, and 500.
   - Database exceptions are rolled back and never leak raw stack traces to the user.

---

## 5. Installation & Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.15)
- pip and standard virtual environment module

### Step 1: Clone or Navigate to Project Directory
```bash
cd /Users/sowbinmr/Desktop/WishVault
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy the documented example environment file:
```bash
cp .env.example .env
```
*(In production, generate a secure random key using `python -c "import secrets; print(secrets.token_hex(32))"` and set `SESSION_COOKIE_SECURE=True` over HTTPS).*

---

## 6. How to Run the Application

Start the Flask development server:
```bash
.venv/bin/python run.py
```
Or using the Flask CLI:
```bash
FLASK_APP=run.py .venv/bin/flask run --port=5001
```

Once running, open your web browser to:
**[http://127.0.0.1:5001](http://127.0.0.1:5001)**

### 🎓 Academic Demonstration Credentials
For grading and evaluation, a pre-seeded account is automatically initialized in development mode:
- **Email Address**: `demo@wishvault.local`
- **Password**: `[Set your local demo password]`
- **Includes**: 7 realistic products in Indian Rupees (Sony headphones, Nike sneakers, Laneige skincare, Apple Watch, Kindle, pastel desk accessories), 3 completed purchase records with dates and amounts, and an active monthly budget configured to display the 80% warning threshold.

---

## 7. How to Run the Test Suite

Execute the full automated Pytest test suite:
```bash
.venv/bin/pytest -v
```

### Run Specific Test Modules
- **Authentication Tests**:
  ```bash
  .venv/bin/pytest tests/test_auth.py -v
  ```
- **IDOR Access Control Tests**:
  ```bash
  .venv/bin/pytest tests/test_authorization.py -v
  ```
- **Product & Input Validation Tests**:
  ```bash
  .venv/bin/pytest tests/test_products.py -v
  ```
- **Shopping Tracker Tests**:
  ```bash
  .venv/bin/pytest tests/test_purchases.py -v
  ```
- **Budget Manager & Threshold Warning Tests**:
  ```bash
  .venv/bin/pytest tests/test_budget.py -v
  ```
- **Security Headers, CSRF, Rate Limiting & SQLi Tests**:
  ```bash
  .venv/bin/pytest tests/test_security.py -v
  ```

---

## 8. Project Directory Structure

```
WishVault/
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules for venv, db, secrets
├── requirements.txt              # Exact pinned project dependencies
├── README.md                     # Comprehensive project documentation
├── SECURITY.md                   # Security controls, threat model, and audits
├── config.py                     # Configuration classes (Dev, Testing, Prod)
├── run.py                        # Application entry point & CLI commands
├── app/
│   ├── __init__.py               # Flask app factory, security headers, error handlers
│   ├── extensions.py             # Extension instances (db, login_manager, csrf, limiter)
│   ├── models/                   # SQLAlchemy relational data models
│   │   ├── __init__.py
│   │   ├── user.py               # User model & password hashing / reset tokens
│   │   ├── collection.py         # Category & collection model
│   │   ├── product.py            # Wishlist product model (INR prices)
│   │   ├── purchase.py           # Shopping tracker purchase record
│   │   └── budget.py             # Monthly shopping budget model
│   ├── forms/                    # WTForms definitions with strict validators
│   │   ├── __init__.py
│   │   ├── auth_forms.py         # Register, Login, Reset Password, Profile forms
│   │   ├── product_forms.py      # Product add/edit form with URL sanitization
│   │   ├── collection_forms.py   # Collection create/edit form
│   │   ├── purchase_forms.py     # Mark purchased & undo forms
│   │   └── budget_forms.py       # Monthly budget setting form
│   ├── routes/                   # Blueprint route controllers
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication, reset tokens, profile
│   │   ├── main.py               # Landing page & dashboard metrics
│   │   ├── products.py           # Wishlist CRUD, search, filter, sort
│   │   ├── collections.py        # Collection management & isolation
│   │   ├── purchases.py          # Shopping tracker & purchase revert
│   │   └── budget.py             # Monthly budget manager & threshold alerts
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py           # URL validator, password complexity, OWASP headers
│   │   └── sample_data.py        # Realistic demo data seeder (INR currency)
│   ├── templates/                # Jinja2 HTML5 templates
│   │   ├── base.html             # Base shell, pastel sidebar, purchase modal, CSRF meta
│   │   ├── landing.html          # Public landing & feature showcase
│   │   ├── auth/                 # Login, Register, Forgot/Reset Password, Profile
│   │   ├── dashboard/            # Key metrics, budget progress meter, recent activity
│   │   ├── products/             # My Wishlist index, details, add/edit form, card macro
│   │   ├── collections/          # Collections grid, collection detail, form
│   │   ├── purchases/            # Shopping tracker & purchase history table
│   │   ├── budget/               # Budget manager, threshold warning, Chart.js trends
│   │   └── errors/               # Custom 400 (CSRF), 403 (IDOR), 404, 429, 500 pages
│   └── static/
│       ├── css/
│       │   └── style.css         # Complete soft pastel design system
│       └── js/
│           └── app.js            # Light-dismiss modals, image fallbacks, mobile drawer
└── tests/                        # Automated Pytest verification suite
    ├── __init__.py
    ├── conftest.py               # Shared test fixtures with StaticPool in-memory DB
    ├── test_auth.py              # Auth, duplicate email, password complexity tests
    ├── test_authorization.py     # IDOR access control tests
    ├── test_products.py          # Product CRUD, search, filter, sort, price validation
    ├── test_purchases.py         # Purchase tracker and undo purchase tests
    ├── test_budget.py            # Budget calculation, 80% warning & exceeded alert tests
    └── test_security.py          # CSRF, rate limiting, SQLi, headers & error tests
```

---

## 9. Known Limitations

- **Simulated Email Delivery**: In development mode, password reset links are displayed directly on the web page and logged to the terminal rather than dispatched via SMTP. In production, configure an SMTP server (e.g. Amazon SES, SendGrid) to deliver reset emails.
- **In-Memory Rate Limiting**: The default rate-limiting backend uses an in-memory storage provider (`memory://`). For multi-instance, clustered production deployments behind a load balancer, configure a shared Redis instance (`redis://`).
