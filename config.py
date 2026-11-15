import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base application configuration."""

    # Security: Secret key for cryptographic signing (sessions, CSRF)
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "wishvault-dev-insecure-key-replace-in-production-abcdef123456"
    )

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'wishvault.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour validity

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in (
        "true",
        "1",
        "yes",
    )
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.environ.get("PERMANENT_SESSION_LIFETIME_HOURS", "2"))
    )

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = os.environ.get(
        "RATELIMIT_DEFAULT", "200 per day;50 per hour"
    )
    RATELIMIT_AUTH = os.environ.get("RATELIMIT_AUTH", "5 per minute")

    # Demo / Seed Settings
    SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@wishvault.io")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo@WishVault2026!")
    DEMO_NAME = os.environ.get("DEMO_NAME", "Aarav Sharma")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with in-memory database."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration with strict security defaults."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # Ensure SECRET_KEY was explicitly set in environment
    if os.environ.get("SECRET_KEY") is None:
        raise ValueError("CRITICAL: SECRET_KEY environment variable must be set in production mode!")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
