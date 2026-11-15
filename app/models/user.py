from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """User account model with secure password hashing and reset tokens."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships with cascade deletion
    collections = db.relationship(
        "Collection",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    products = db.relationship(
        "Product",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    purchases = db.relationship(
        "Purchase",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    budgets = db.relationship(
        "Budget",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password: str) -> None:
        """Hash and set user password using Werkzeug security utility."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, secret_key: str, expires_sec: int = 3600) -> str:
        """Generate a cryptographically signed, time-limited password reset token."""
        serializer = URLSafeTimedSerializer(secret_key)
        return serializer.dumps({"user_id": self.id}, salt="password-reset-salt")

    @staticmethod
    def verify_reset_token(token: str, secret_key: str, max_age: int = 3600):
        """Verify the password reset token and return the associated User or None."""
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            data = serializer.loads(token, salt="password-reset-salt", max_age=max_age)
        except (SignatureExpired, BadSignature, Exception):
            return None
        return db.session.get(User, data.get("user_id"))

    def __repr__(self) -> str:
        # Never log password hash or sensitive tokens
        return f"<User id={self.id} email='{self.email}'>"


@login_manager.user_loader
def load_user(user_id: str):
    """Load user by ID for Flask-Login session management."""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None
