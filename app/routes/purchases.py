from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
)
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.product import Product
from app.models.purchase import Purchase
from app.forms.purchase_forms import PurchaseForm, UndoPurchaseForm

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")


@purchases_bp.route("/")
@login_required
def index():
    """
    Shopping Tracker: displays full purchase history for the logged-in user.
    Shows total spending, purchase breakdown, and lets users undo purchases.
    """
    user_id = current_user.id

    purchases = (
        Purchase.query.filter_by(user_id=user_id)
        .order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())
        .all()
    )

    total_spent_val = (
        Purchase.query.with_entities(func.sum(Purchase.actual_amount))
        .filter_by(user_id=user_id)
        .scalar()
    )
    total_spent = float(total_spent_val or 0.0)

    undo_form = UndoPurchaseForm()

    return render_template(
        "purchases/index.html",
        purchases=purchases,
        total_spent=total_spent,
        undo_form=undo_form,
    )


@purchases_bp.route("/mark/<int:product_id>", methods=["POST"])
@login_required
def mark_purchased(product_id: int):
    """
    Mark a wishlist item as purchased with actual amount and date.
    Strictly verifies ownership to eliminate IDOR vulnerabilities.
    """
    product = Product.query.get_or_404(product_id)

    # IDOR Check: Ensure user owns this product
    if product.user_id != current_user.id:
        abort(403)

    if product.is_purchased:
        flash(f"'{product.name}' is already marked as purchased.", "info")
        return redirect(request.referrer or url_for("products.index"))

    form = PurchaseForm()
    if form.validate_on_submit():
        purchase = Purchase(
            user_id=current_user.id,
            product_id=product.id,
            actual_amount=form.actual_amount.data,
            purchase_date=form.purchase_date.data,
            notes=form.notes.data.strip() if form.notes.data else None,
        )
        product.is_purchased = True

        db.session.add(purchase)
        db.session.commit()
        flash(
            f"🎉 Congratulations! '{product.name}' was marked as purchased for ₹{float(purchase.actual_amount):,.2f}.",
            "success",
        )
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Purchase Error: {error}", "danger")

    return redirect(request.referrer or url_for("purchases.index"))


@purchases_bp.route("/undo/<int:purchase_id>", methods=["POST"])
@login_required
def undo_purchase(purchase_id: int):
    """
    Revert an accidental purchase marking.
    Restores product to wishlist, deletes purchase record, updates budget stats.
    Strictly verifies ownership to prevent IDOR attacks.
    """
    purchase = Purchase.query.get_or_404(purchase_id)

    # IDOR Check: Ensure purchase belongs to current user
    if purchase.user_id != current_user.id:
        abort(403)

    product = db.session.get(Product, purchase.product_id)
    if product and product.user_id == current_user.id:
        product.is_purchased = False

    product_name = product.name if product else "Product"
    db.session.delete(purchase)
    db.session.commit()

    flash(
        f"Purchase for '{product_name}' was undone. Item is restored to active wishlist.",
        "info",
    )
    return redirect(request.referrer or url_for("purchases.index"))
