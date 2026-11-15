from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    """Wishlist product item model."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    purchase_url = db.Column(db.String(500), nullable=True)
    is_purchased = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 1-to-1 relationship with purchase record when marked as purchased
    purchase = db.relationship(
        "Purchase",
        backref="product",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def formatted_price(self) -> str:
        """Return formatted price with Indian Rupee symbol."""
        try:
            return f"₹{float(self.price):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    def __repr__(self) -> str:
        return f"<Product id={self.id} user_id={self.user_id} name='{self.name}' price={self.price}>"
