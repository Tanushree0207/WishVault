from datetime import datetime, date, timezone
from app.extensions import db


class Purchase(db.Model):
    """Purchase tracking model recording completed wishlist purchases."""

    __tablename__ = "purchases"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    purchase_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    actual_amount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    @property
    def formatted_amount(self) -> str:
        """Return formatted actual amount with Indian Rupee symbol."""
        try:
            return f"₹{float(self.actual_amount):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    def __repr__(self) -> str:
        return f"<Purchase id={self.id} user_id={self.user_id} product_id={self.product_id} amount={self.actual_amount}>"
