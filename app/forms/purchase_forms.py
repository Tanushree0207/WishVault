from datetime import date
from flask_wtf import FlaskForm
from wtforms import DecimalField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class PurchaseForm(FlaskForm):
    """Form to mark a product as purchased and record purchase details."""

    actual_amount = DecimalField(
        "Actual Amount Paid (INR ₹)",
        places=2,
        validators=[
            DataRequired(message="Please enter the actual amount paid."),
            NumberRange(
                min=0.01,
                max=10000000.00,
                message="Purchase amount must be positive.",
            ),
        ],
    )
    purchase_date = DateField(
        "Purchase Date",
        default=date.today,
        validators=[DataRequired(message="Purchase date is required.")],
    )
    notes = TextAreaField(
        "Purchase Notes / Order Reference",
        validators=[
            Optional(),
            Length(max=500, message="Notes cannot exceed 500 characters."),
        ],
    )
    submit = SubmitField("Confirm Purchase")


class UndoPurchaseForm(FlaskForm):
    """CSRF-protected form to revert an accidental purchase."""

    submit = SubmitField("Undo Purchase")
