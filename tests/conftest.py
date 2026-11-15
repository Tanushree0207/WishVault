import pytest
from sqlalchemy.pool import StaticPool
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.utils.sample_data import create_default_collections_for_user


@pytest.fixture
def app():
    """Create and configure a testing Flask application with shared in-memory SQLite database."""
    test_app = create_app("testing")
    test_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            },
        }
    )
    return test_app


@pytest.fixture(autouse=True)
def app_context(app):
    """Keep application context and clean database schema active for each test."""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Test client for unauthenticated requests."""
    return app.test_client()


@pytest.fixture
def user_a(app):
    """Fixture providing user A with default collections."""
    user = User(full_name="User Alpha", email="alpha@wishvault.io")
    user.set_password("AlphaPass@2026!")
    _db.session.add(user)
    _db.session.commit()
    create_default_collections_for_user(user)
    return user


@pytest.fixture
def user_b(app):
    """Fixture providing user B with default collections."""
    user = User(full_name="User Beta", email="beta@wishvault.io")
    user.set_password("BetaPass@2026!")
    _db.session.add(user)
    _db.session.commit()
    create_default_collections_for_user(user)
    return user


@pytest.fixture
def auth_client_a(client, user_a):
    """Client authenticated as User Alpha."""
    client.post(
        "/auth/login",
        data={"email": "alpha@wishvault.io", "password": "AlphaPass@2026!"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def auth_client_b(app, user_b):
    """Client authenticated as User Beta."""
    b_client = app.test_client()
    b_client.post(
        "/auth/login",
        data={"email": "beta@wishvault.io", "password": "BetaPass@2026!"},
        follow_redirects=True,
    )
    return b_client
