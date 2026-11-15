from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.products import products_bp
from app.routes.collections import collections_bp
from app.routes.purchases import purchases_bp
from app.routes.budget import budget_bp

__all__ = [
    "auth_bp",
    "main_bp",
    "products_bp",
    "collections_bp",
    "purchases_bp",
    "budget_bp",
]
