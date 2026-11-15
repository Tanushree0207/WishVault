from datetime import datetime, timezone
from app.extensions import db


class Budget(db.Model):
    """Monthly shopping budget model."""

    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1 to 12
    monthly_budget = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "year", "month", name="uq_user_monthly_budget"
        ),
    )

    @property
    def formatted_budget(self) -> str:
        """Return formatted monthly budget with Indian Rupee symbol."""
        try:
            return f"₹{float(self.monthly_budget):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    def __repr__(self) -> str:
        return f"<Budget id={self.id} user_id={self.user_id} year={self.year} month={self.month} budget={self.monthly_budget}>"
