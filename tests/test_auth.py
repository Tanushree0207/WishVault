from app.models.user import User


def test_successful_registration(client, app):
    """Test standard user registration creates hashed credentials and default collections."""
    res = client.post(
        "/auth/register",
        data={
            "full_name": "Rohan Gupta",
            "email": "rohan@wishvault.io",
            "password": "SecurePass@123",
            "confirm_password": "SecurePass@123",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Account successfully created" in res.data

    with app.app_context():
        user = User.query.filter_by(email="rohan@wishvault.io").first()
        assert user is not None
        assert user.full_name == "Rohan Gupta"
        # Password MUST be hashed with Werkzeug, never stored plaintext
        assert user.password_hash != "SecurePass@123"
        assert user.check_password("SecurePass@123") is True
        assert user.check_password("WrongPassword") is False
        # Verify default collections were created
        assert user.collections.count() == 7


def test_duplicate_registration_rejection(client, user_a):
    """Test duplicate email registration is rejected."""
    res = client.post(
        "/auth/register",
        data={
            "full_name": "Duplicate User",
            "email": "alpha@wishvault.io",  # Same as user_a
            "password": "NewPassword@123",
            "confirm_password": "NewPassword@123",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"An account with this email address already exists" in res.data


def test_weak_password_rejection(client):
    """Test password strength validation rejects weak passwords."""
    # 1. Too short
    res1 = client.post(
        "/auth/register",
        data={
            "full_name": "Test User",
            "email": "short@wishvault.io",
            "password": "Sh1!",
            "confirm_password": "Sh1!",
        },
        follow_redirects=True,
    )
    assert b"at least 8 characters long" in res1.data

    # 2. No special character
    res2 = client.post(
        "/auth/register",
        data={
            "full_name": "Test User",
            "email": "nospecial@wishvault.io",
            "password": "Password1234",
            "confirm_password": "Password1234",
        },
        follow_redirects=True,
    )
    assert b"special character" in res2.data

    # 3. No uppercase
    res3 = client.post(
        "/auth/register",
        data={
            "full_name": "Test User",
            "email": "noupper@wishvault.io",
            "password": "password123!",
            "confirm_password": "password123!",
        },
        follow_redirects=True,
    )
    assert b"uppercase letter" in res3.data


def test_successful_login(client, user_a):
    """Test valid credentials authenticate successfully and redirect."""
    res = client.post(
        "/auth/login",
        data={"email": "alpha@wishvault.io", "password": "AlphaPass@2026!"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Welcome back, User" in res.data


def test_invalid_password_rejection(client, user_a):
    """Test invalid password returns generic error and denies access."""
    res = client.post(
        "/auth/login",
        data={"email": "alpha@wishvault.io", "password": "WrongPassword@123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Invalid email address or password" in res.data


def test_nonexistent_user_login(client):
    """Test logging in with unregistered email returns generic error without leaking user existence."""
    res = client.post(
        "/auth/login",
        data={"email": "doesnotexist@wishvault.io", "password": "SomePass@123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Invalid email address or password" in res.data


def test_logout(auth_client_a):
    """Test logout terminates user session."""
    res = auth_client_a.post("/auth/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"You have been signed out successfully" in res.data

    # Accessing protected page should redirect to login
    dash_res = auth_client_a.get("/dashboard", follow_redirects=True)
    assert b"Please log in to access your WishVault" in dash_res.data


def test_unauthorized_access_prevention(client):
    """Test unauthenticated users cannot access protected views."""
    protected_urls = [
        "/dashboard",
        "/products/",
        "/products/new",
        "/collections/",
        "/purchases/",
        "/budget/",
        "/auth/profile",
    ]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code == 302
        assert "/auth/login" in res.headers["Location"]


def test_password_reset_token_workflow(app, client, user_a):
    """Test password reset token generation, verification, and password change."""
    with app.app_context():
        token = user_a.get_reset_token(app.config["SECRET_KEY"])
        assert token is not None

        # Verify token returns the user
        verified = User.verify_reset_token(token, app.config["SECRET_KEY"])
        assert verified.id == user_a.id

        # Invalid token fails
        invalid = User.verify_reset_token("invalid-garbage-token", app.config["SECRET_KEY"])
        assert invalid is None

    # Test submitting reset password form
    res = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "BrandNewPass@2026!", "confirm_password": "BrandNewPass@2026!"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Your password has been reset successfully" in res.data

    # Log in with the new password
    login_res = client.post(
        "/auth/login",
        data={"email": "alpha@wishvault.io", "password": "BrandNewPass@2026!"},
        follow_redirects=True,
    )
    assert b"Welcome back" in login_res.data
