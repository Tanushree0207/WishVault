from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class CollectionForm(FlaskForm):
    """Collection creation and edit form."""

    name = StringField(
        "Collection Name",
        validators=[
            DataRequired(message="Collection name is required."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters."),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[
            Optional(),
            Length(max=255, message="Description cannot exceed 255 characters."),
        ],
    )
    icon = SelectField(
        "Icon Badge",
        choices=[
            ("sparkles", "✨ Sparkles / Favorites"),
            ("shirt", "👗 Fashion & Style"),
            ("laptop", "💻 Electronics & Tech"),
            ("heart", "💄 Beauty & Wellness"),
            ("book", "📚 Books & Learning"),
            ("watch", "⌚ Accessories & Jewelry"),
            ("home", "🏡 Home & Living"),
            ("gift", "🎁 Gifts & Wishlist"),
            ("tag", "🏷️ General Collection"),
        ],
        default="sparkles",
    )
    color = SelectField(
        "Theme Color",
        choices=[
            ("lavender", "Lavender Purple"),
            ("blush", "Blush Pink"),
            ("peach", "Soft Peach"),
            ("mint", "Pastel Mint"),
            ("sky", "Powder Sky"),
            ("rose", "Dusty Rose"),
        ],
        default="lavender",
    )
    submit = SubmitField("Save Collection")
