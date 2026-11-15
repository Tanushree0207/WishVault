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
from app.extensions import db
from app.models.product import Product
from app.models.collection import Collection
from app.forms.product_forms import ProductForm
from app.forms.purchase_forms import PurchaseForm

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _get_user_collection_choices(user_id: int):
    """Fetch user's collections to populate form choices safely."""
    collections = (
        Collection.query.filter_by(user_id=user_id)
        .order_by(Collection.name.asc())
        .all()
    )
    choices = [(0, "No Collection (General)")]
    for col in collections:
        choices.append((col.id, col.name))
    return choices


@products_bp.route("/")
@login_required
def index():
    """
    List user's products with search, category filtering, and sorting.
    Guarantees user isolation (IDOR defense) by filtering strictly on current_user.id.
    """
    user_id = current_user.id

    # Query parameters
    search_query = request.args.get("q", "").strip()
    collection_id = request.args.get("collection", type=int)
    status_filter = request.args.get("status", "all")  # all, wishlist, purchased
    sort_by = request.args.get("sort", "newest")  # newest, oldest, price_low, price_high

    # Base query restricted strictly to current user's products
    query = Product.query.filter_by(user_id=user_id)

    # Search filter (SQLAlchemy parameterized - immune to SQL injection)
    if search_query:
        # Escape wildcard characters for like query if needed
        safe_search = f"%{search_query}%"
        query = query.filter(
            (Product.name.ilike(safe_search))
            | (Product.description.ilike(safe_search))
        )

    # Collection filter
    if collection_id and collection_id > 0:
        query = query.filter(Product.collection_id == collection_id)

    # Status filter
    if status_filter == "wishlist":
        query = query.filter(Product.is_purchased.is_(False))
    elif status_filter == "purchased":
        query = query.filter(Product.is_purchased.is_(True))

    # Sorting
    if sort_by == "oldest":
        query = query.order_by(Product.created_at.asc())
    elif sort_by == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_high":
        query = query.order_by(Product.price.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    user_collections = (
        Collection.query.filter_by(user_id=user_id)
        .order_by(Collection.name.asc())
        .all()
    )
    purchase_form = PurchaseForm()

    return render_template(
        "products/index.html",
        products=products,
        collections=user_collections,
        search_query=search_query,
        selected_collection=collection_id,
        selected_status=status_filter,
        selected_sort=sort_by,
        purchase_form=purchase_form,
    )


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Add a new product to the current user's wishlist."""
    form = ProductForm()
    form.collection_id.choices = _get_user_collection_choices(current_user.id)

    if form.validate_on_submit():
        col_id = form.collection_id.data if form.collection_id.data != 0 else None

        # Verify collection ownership if specified
        if col_id:
            col = Collection.query.filter_by(
                id=col_id, user_id=current_user.id
            ).first()
            if not col:
                flash("Selected collection is invalid.", "danger")
                return render_template(
                    "products/form.html", form=form, is_edit=False
                )

        product = Product(
            user_id=current_user.id,
            collection_id=col_id,
            name=form.name.data.strip(),
            price=form.price.data,
            description=form.description.data.strip()
            if form.description.data
            else None,
            image_url=form.image_url.data.strip() if form.image_url.data else None,
            purchase_url=form.purchase_url.data.strip()
            if form.purchase_url.data
            else None,
            is_purchased=False,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"'{product.name}' was added to your WishVault!", "success")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", form=form, is_edit=False)


@products_bp.route("/<int:product_id>")
@login_required
def detail(product_id: int):
    """View product details with strict IDOR verification."""
    product = Product.query.get_or_404(product_id)

    # Strict Access Control: User can only view their own products
    if product.user_id != current_user.id:
        abort(403)

    purchase_form = PurchaseForm()
    return render_template(
        "products/detail.html", product=product, purchase_form=purchase_form
    )


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id: int):
    """Edit existing product with strict IDOR verification."""
    product = Product.query.get_or_404(product_id)

    # IDOR Check: Ensure user owns this product
    if product.user_id != current_user.id:
        abort(403)

    form = ProductForm()
    form.collection_id.choices = _get_user_collection_choices(current_user.id)

    if form.validate_on_submit():
        col_id = form.collection_id.data if form.collection_id.data != 0 else None

        # Verify collection ownership if specified
        if col_id:
            col = Collection.query.filter_by(
                id=col_id, user_id=current_user.id
            ).first()
            if not col:
                flash("Selected collection is invalid.", "danger")
                return render_template(
                    "products/form.html",
                    form=form,
                    product=product,
                    is_edit=True,
                )

        product.name = form.name.data.strip()
        product.price = form.price.data
        product.collection_id = col_id
        product.description = (
            form.description.data.strip() if form.description.data else None
        )
        product.image_url = (
            form.image_url.data.strip() if form.image_url.data else None
        )
        product.purchase_url = (
            form.purchase_url.data.strip() if form.purchase_url.data else None
        )

        db.session.commit()
        flash(f"'{product.name}' has been updated.", "success")
        return redirect(url_for("products.detail", product_id=product.id))

    if request.method == "GET":
        form.name.data = product.name
        form.price.data = product.price
        form.collection_id.data = product.collection_id or 0
        form.description.data = product.description
        form.image_url.data = product.image_url
        form.purchase_url.data = product.purchase_url

    return render_template(
        "products/form.html", form=form, product=product, is_edit=True
    )


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
def delete(product_id: int):
    """Delete product with strict IDOR verification and CSRF protection."""
    product = Product.query.get_or_404(product_id)

    # IDOR Check
    if product.user_id != current_user.id:
        abort(403)

    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"'{name}' was removed from your WishVault.", "info")
    return redirect(url_for("products.index"))
