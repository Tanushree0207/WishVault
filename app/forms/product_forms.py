from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Optional, Length, NumberRange, ValidationError
from app.utils.security import is_safe_url


class ProductForm(FlaskForm):
    """Product creation and edit form with strict price and URL validation."""

    name = StringField(
        "Product Name",
        validators=[
            DataRequired(message="Product name is required."),
            Length(min=2, max=150, message="Name must be between 2 and 150 characters."),
        ],
    )
    price = DecimalField(
        "Price (INR ₹)",
        places=2,
        validators=[
            InputRequired(message="Price is required."),
            NumberRange(
                min=0.01,
                max=10000000.00,
                message="Price must be a positive amount up to ₹1,00,00,000.",
            ),
        ],
    )
    collection_id = SelectField(
        "Collection / Category",
        coerce=int,
        validators=[Optional()],
    )
    description = TextAreaField(
        "Description & Notes",
        validators=[
            Optional(),
            Length(max=1000, message="Description cannot exceed 1000 characters."),
        ],
    )
    image_url = StringField(
        "Product Image URL",
        validators=[
            Optional(),
            Length(max=500, message="Image URL cannot exceed 500 characters."),
        ],
    )
    purchase_url = StringField(
        "Product Purchase / Store Link",
        validators=[
            Optional(),
            Length(max=500, message="Store URL cannot exceed 500 characters."),
        ],
    )
    submit = SubmitField("Save to Wishlist")

    def validate_image_url(self, field):
        """Reject dangerous URL schemes or malformed URLs."""
        if field.data and not is_safe_url(field.data):
            raise ValidationError(
                "Invalid image URL. Only safe http:// and https:// URLs are permitted."
            )

    def validate_purchase_url(self, field):
        """Reject dangerous URL schemes or javascript: injection."""
        if field.data and not is_safe_url(field.data):
            raise ValidationError(
                "Invalid store URL. Only safe http:// and https:// URLs are permitted."
            )
