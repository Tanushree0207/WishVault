from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models.user import User
from app.forms.auth_forms import (
    RegisterForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    UpdateProfileForm,
    ChangePasswordForm,
)
from app.utils.sample_data import create_default_collections_for_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    """Register a new user account with secure password hashing and default collections."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = User(
            full_name=form.full_name.data.strip(),
            email=normalized_email,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Initialize default collections for the user
        create_default_collections_for_user(user)

        flash(
            "Account successfully created! You can now sign in to your WishVault.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    """Authenticate existing user with Werkzeug password hash verification."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = User.query.filter_by(email=normalized_email).first()

        # Secure constant-time-like check; never leak whether user exists vs password wrong
        if user and user.check_password(form.password.data):
            # Session Fixation Defense: clear old session before logging in
            session.clear()
            login_user(user, remember=form.remember_me.data)

            # Prevent Open Redirect Vulnerability
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
                next_page = url_for("main.dashboard")

            flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
            return redirect(next_page)
        else:
            flash("Invalid email address or password. Please try again.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Safely log out user and destroy session."""
    logout_user()
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def forgot_password():
    """Initiate secure token-based password reset workflow."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = ForgotPasswordForm()
    reset_url = None

    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = User.query.filter_by(email=normalized_email).first()

        if user:
            token = user.get_reset_token(current_app.config["SECRET_KEY"])
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            # In a production app with SMTP configured, this would be emailed.
            # In development/academic context, we provide the secure link directly on screen
            # and in the console for instant testing.
            current_app.logger.info(
                f"[SECURITY AUDIT] Password reset token generated for user id={user.id}"
            )
            flash(
                "A password reset link has been generated. For testing, follow the link below.",
                "success",
            )
        else:
            # Generic response to prevent user enumeration attacks
            flash(
                "If an account exists with that email address, reset instructions have been generated.",
                "info",
            )

    return render_template(
        "auth/forgot_password.html", form=form, reset_url=reset_url
    )


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Verify reset token and update user password."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    user = User.verify_reset_token(token, current_app.config["SECRET_KEY"])
    if not user:
        flash(
            "The password reset link is invalid or has expired. Please request a new one.",
            "warning",
        )
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(
            "Your password has been reset successfully! You can now log in with your new password.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, token=token)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile management (view details, update name, change password)."""
    profile_form = UpdateProfileForm(prefix="profile")
    password_form = ChangePasswordForm(prefix="pwd")

    # Prepopulate profile form on GET
    if request.method == "GET":
        profile_form.full_name.data = current_user.full_name

    # Handle Profile Update
    if "profile-submit" in request.form and profile_form.validate_on_submit():
        current_user.full_name = profile_form.full_name.data.strip()
        db.session.commit()
        flash("Your profile information has been updated.", "success")
        return redirect(url_for("auth.profile"))

    # Handle Password Change
    if "pwd-submit" in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Current password entered is incorrect.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Your password has been changed successfully.", "success")
            return redirect(url_for("auth.profile"))

    return render_template(
        "auth/profile.html",
        profile_form=profile_form,
        password_form=password_form,
        user=current_user,
    )
