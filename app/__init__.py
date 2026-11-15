import os
import logging
from flask import Flask, render_template, request, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask_wtf.csrf import CSRFError

from config import config_by_name
from app.extensions import db, login_manager, csrf, limiter
from app.utils.security import get_security_headers


def create_app(config_name: str = "default") -> Flask:
    """Application factory for WishVault."""
    app = Flask(__name__)

    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Configure secure logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        )
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Enforce SQLite foreign key constraints
    with app.app_context():
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                pass

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.products import products_bp
    from app.routes.collections import collections_bp
    from app.routes.purchases import purchases_bp
    from app.routes.budget import budget_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(budget_bp)

    # Register Security Headers Hook
    @app.after_request
    def apply_security_headers(response):
        """Inject strict OWASP-recommended security headers into every HTTP response."""
        is_production = not app.debug and not app.testing
        headers = get_security_headers(is_production=is_production)
        for key, value in headers.items():
            response.headers[key] = value
        return response

    # Register Error Handlers (never leak internal stack traces)
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.warning(f"400 Bad Request at {request.path}: {error}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Bad Request", "message": "Invalid request submission."}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        app.logger.warning(f"CSRF validation failed at {request.path} from IP {request.remote_addr}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "CSRF Error", "message": "Invalid or missing CSRF security token."}), 400
        return render_template(
            "errors/400.html",
            custom_title="Security Token Error (CSRF)",
            custom_message="Your security session token has expired or is invalid. Please refresh the page and try again.",
        ), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 Forbidden at {request.path} from IP {request.remote_addr}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Forbidden", "message": "You do not have permission to access this resource."}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Not Found", "message": "The requested resource was not found."}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def ratelimit_handler(error):
        app.logger.warning(f"429 Rate Limit Exceeded at {request.path} by {request.remote_addr}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Too Many Requests", "message": "Rate limit exceeded. Please wait a moment."}), 429
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Internal Server Error at {request.path}: {error}")
        # Rollback any failed database transaction
        db.session.rollback()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred. Please try again later."}), 500
        return render_template("errors/500.html"), 500

    # Custom Jinja Template Filters
    @app.template_filter("currency_inr")
    def currency_inr(value):
        """Format number as Indian Rupee (₹)."""
        try:
            val = float(value)
            return f"₹{val:,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    # Context Processor for Global Template Variables
    @app.context_processor
    def inject_global_vars():
        return {
            "app_name": "WishVault",
            "app_tagline": "Your wishes, beautifully organized.",
        }

    # Auto-initialize database tables and demo seed in development
    with app.app_context():
        db.create_all()
        if app.config.get("SEED_DEMO_DATA") and not app.testing:
            try:
                from app.utils.sample_data import seed_sample_data
                seed_sample_data(app)
            except Exception as e:
                app.logger.warning(f"Sample data seeding notice: {e}")

    return app
