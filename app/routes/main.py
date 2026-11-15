from datetime import date
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app.models.product import Product
from app.models.collection import Collection
from app.models.purchase import Purchase
from app.models.budget import Budget

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page or direct redirect to dashboard for logged-in users."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    User dashboard displaying actual database metrics:
    - Total saved products
    - Number of collections
    - Number of purchased products
    - Total lifetime and monthly expenditure
    - Remaining monthly budget with 80% warning and alert
    - Recently added products
    - Recently purchased products
    """
    user_id = current_user.id
    today = date.today()
    current_year = today.year
    current_month = today.month

    # 1. Product & Collection counts
    total_saved = Product.query.filter_by(user_id=user_id).count()
    total_collections = Collection.query.filter_by(user_id=user_id).count()
    purchased_count = Product.query.filter_by(
        user_id=user_id, is_purchased=True
    ).count()
    active_wishlist_count = Product.query.filter_by(
        user_id=user_id, is_purchased=False
    ).count()

    # 2. Total lifetime expenditure
    lifetime_spent_query = (
        Purchase.query.with_entities(func.sum(Purchase.actual_amount))
        .filter(Purchase.user_id == user_id)
        .scalar()
    )
    total_purchased_amount = float(lifetime_spent_query or 0.0)

    # 3. Current month expenditure
    monthly_spent_query = (
        Purchase.query.with_entities(func.sum(Purchase.actual_amount))
        .filter(
            Purchase.user_id == user_id,
            extract("year", Purchase.purchase_date) == current_year,
            extract("month", Purchase.purchase_date) == current_month,
        )
        .scalar()
    )
    monthly_spent = float(monthly_spent_query or 0.0)

    # 4. Monthly budget calculation
    current_budget_record = Budget.query.filter_by(
        user_id=user_id, year=current_year, month=current_month
    ).first()

    monthly_budget = (
        float(current_budget_record.monthly_budget)
        if current_budget_record
        else 0.0
    )

    remaining_budget = monthly_budget - monthly_spent if monthly_budget > 0 else 0.0
    spent_percentage = (
        round((monthly_spent / monthly_budget) * 100, 1) if monthly_budget > 0 else 0.0
    )

    # Status flags
    is_budget_exceeded = monthly_budget > 0 and monthly_spent > monthly_budget
    is_budget_warning = (
        monthly_budget > 0
        and not is_budget_exceeded
        and spent_percentage >= 80.0
    )

    # 5. Recently added products (limit 5)
    recent_products = (
        Product.query.filter_by(user_id=user_id)
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )

    # 6. Recently purchased products (limit 5)
    recent_purchases = (
        Purchase.query.filter_by(user_id=user_id)
        .order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        user=current_user,
        total_saved=total_saved,
        total_collections=total_collections,
        purchased_count=purchased_count,
        active_wishlist_count=active_wishlist_count,
        total_purchased_amount=total_purchased_amount,
        monthly_spent=monthly_spent,
        monthly_budget=monthly_budget,
        remaining_budget=remaining_budget,
        spent_percentage=spent_percentage,
        is_budget_warning=is_budget_warning,
        is_budget_exceeded=is_budget_exceeded,
        recent_products=recent_products,
        recent_purchases=recent_purchases,
        current_month_name=today.strftime("%B"),
        current_year=current_year,
    )
