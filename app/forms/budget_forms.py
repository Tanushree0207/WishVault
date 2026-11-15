from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class BudgetForm(FlaskForm):
    """Monthly shopping budget setting form."""

    monthly_budget = DecimalField(
        "Monthly Budget (INR ₹)",
        places=2,
        validators=[
            DataRequired(message="Please enter your monthly budget."),
            NumberRange(
                min=0.00,
                max=100000000.00,
                message="Budget must be 0 or a positive amount.",
            ),
        ],
    )
    month = SelectField(
        "Month",
        coerce=int,
        choices=[
            (1, "January"),
            (2, "February"),
            (3, "March"),
            (4, "April"),
            (5, "May"),
            (6, "June"),
            (7, "July"),
            (8, "August"),
            (9, "September"),
            (10, "October"),
            (11, "November"),
            (12, "December"),
        ],
        validators=[DataRequired()],
    )
    year = IntegerField(
        "Year",
        validators=[
            DataRequired(message="Year is required."),
            NumberRange(min=2020, max=2100, message="Please enter a valid year."),
        ],
    )
    submit = SubmitField("Save Monthly Budget")
