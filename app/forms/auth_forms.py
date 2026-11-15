from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User
from app.utils.security import validate_password_strength


class RegisterForm(FlaskForm):
    """User registration form with email uniqueness and password complexity validation."""

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Please enter your full name."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters."),
        ],
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(check_deliverability=False, message="Please enter a valid email address."),
            Length(max=255, message="Email cannot exceed 255 characters."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please choose a password."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create WishVault Account")

    def validate_password(self, field):
        """Verify password meets security complexity standards."""
        is_valid, msg = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(msg)

    def validate_email(self, field):
        """Prevent duplicate email registrations."""
        normalized_email = field.data.strip().lower()
        existing = User.query.filter_by(email=normalized_email).first()
        if existing:
            raise ValidationError("An account with this email address already exists.")


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(check_deliverability=False, message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter your password."),
        ],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In to WishVault")


class ForgotPasswordForm(FlaskForm):
    """Password reset request form."""

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Please enter your registered email address."),
            Email(check_deliverability=False, message="Please enter a valid email address."),
        ],
    )
    submit = SubmitField("Send Reset Instructions")


class ResetPasswordForm(FlaskForm):
    """Password reset form using secure token."""

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Please enter a new password."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Update Password")

    def validate_password(self, field):
        """Enforce password complexity for password reset."""
        is_valid, msg = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(msg)


class UpdateProfileForm(FlaskForm):
    """User profile update form."""

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Please enter your full name."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters."),
        ],
    )
    submit = SubmitField("Save Profile Changes")


class ChangePasswordForm(FlaskForm):
    """Change password form from user profile."""

    current_password = PasswordField(
        "Current Password",
        validators=[
            DataRequired(message="Please enter your current password."),
        ],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Please enter a new password."),
        ],
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo("new_password", message="New passwords must match."),
        ],
    )
    submit = SubmitField("Change Password")

    def validate_new_password(self, field):
        """Verify new password meets security standards."""
        is_valid, msg = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(msg)
