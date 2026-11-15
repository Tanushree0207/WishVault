from datetime import datetime, timezone
from app.extensions import db


class Collection(db.Model):
    """Collection model for organizing products into custom or default categories."""

    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default="sparkles", nullable=False)
    color = db.Column(db.String(30), default="lavender", nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship to products
    products = db.relationship(
        "Product",
        backref="collection",
        lazy="dynamic",
        passive_deletes=True,
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "name", name="uq_user_collection_name"),
    )

    def __repr__(self) -> str:
        return f"<Collection id={self.id} user_id={self.user_id} name='{self.name}'>"
