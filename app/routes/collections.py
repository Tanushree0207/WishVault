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
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.collection import Collection
from app.models.product import Product
from app.forms.collection_forms import CollectionForm
from app.forms.purchase_forms import PurchaseForm

collections_bp = Blueprint("collections", __name__, url_prefix="/collections")


@collections_bp.route("/")
@login_required
def index():
    """Display user's collections with product counts."""
    user_id = current_user.id
    collections = (
        Collection.query.filter_by(user_id=user_id)
        .order_by(Collection.is_default.desc(), Collection.name.asc())
        .all()
    )
    # Also count uncategorized products
    uncategorized_count = Product.query.filter_by(
        user_id=user_id, collection_id=None
    ).count()

    return render_template(
        "collections/index.html",
        collections=collections,
        uncategorized_count=uncategorized_count,
    )


@collections_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Create a new custom collection."""
    form = CollectionForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        existing = Collection.query.filter_by(
            user_id=current_user.id, name=name
        ).first()
        if existing:
            flash(f"A collection named '{name}' already exists in your vault.", "warning")
            return render_template(
                "collections/form.html", form=form, is_edit=False
            )

        collection = Collection(
            user_id=current_user.id,
            name=name,
            description=form.description.data.strip()
            if form.description.data
            else None,
            icon=form.icon.data,
            color=form.color.data,
            is_default=False,
        )
        db.session.add(collection)
        try:
            db.session.commit()
            flash(f"Collection '{collection.name}' created successfully!", "success")
            return redirect(url_for("collections.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Failed to create collection. Please try a different name.", "danger")

    return render_template("collections/form.html", form=form, is_edit=False)


@collections_bp.route("/<int:collection_id>")
@login_required
def detail(collection_id: int):
    """View products within a collection with strict IDOR verification."""
    collection = Collection.query.get_or_404(collection_id)

    # IDOR Check: Ensure user owns this collection
    if collection.user_id != current_user.id:
        abort(403)

    products = (
        Product.query.filter_by(
            user_id=current_user.id, collection_id=collection.id
        )
        .order_by(Product.created_at.desc())
        .all()
    )
    purchase_form = PurchaseForm()

    return render_template(
        "collections/detail.html",
        collection=collection,
        products=products,
        purchase_form=purchase_form,
    )


@collections_bp.route("/<int:collection_id>/edit", methods=["GET", "POST"])
@login_required
def edit(collection_id: int):
    """Edit custom collection details with strict IDOR verification."""
    collection = Collection.query.get_or_404(collection_id)

    # IDOR Check
    if collection.user_id != current_user.id:
        abort(403)

    form = CollectionForm()

    if form.validate_on_submit():
        new_name = form.name.data.strip()
        # If renamed, check for collision with another of user's collections
        if new_name != collection.name:
            existing = Collection.query.filter_by(
                user_id=current_user.id, name=new_name
            ).first()
            if existing:
                flash(
                    f"A collection named '{new_name}' already exists in your vault.",
                    "warning",
                )
                return render_template(
                    "collections/form.html",
                    form=form,
                    collection=collection,
                    is_edit=True,
                )

        collection.name = new_name
        collection.description = (
            form.description.data.strip() if form.description.data else None
        )
        collection.icon = form.icon.data
        collection.color = form.color.data

        db.session.commit()
        flash(f"Collection '{collection.name}' has been updated.", "success")
        return redirect(url_for("collections.index"))

    if request.method == "GET":
        form.name.data = collection.name
        form.description.data = collection.description
        form.icon.data = collection.icon
        form.color.data = collection.color

    return render_template(
        "collections/form.html",
        form=form,
        collection=collection,
        is_edit=True,
    )


@collections_bp.route("/<int:collection_id>/delete", methods=["POST"])
@login_required
def delete(collection_id: int):
    """Delete collection with strict IDOR check (products become uncategorized)."""
    collection = Collection.query.get_or_404(collection_id)

    # IDOR Check
    if collection.user_id != current_user.id:
        abort(403)

    name = collection.name
    # Unlink products so they are kept in wishlist
    Product.query.filter_by(collection_id=collection.id).update(
        {"collection_id": None}
    )
    db.session.delete(collection)
    db.session.commit()
    flash(
        f"Collection '{name}' was deleted. Its products were moved to Uncategorized.",
        "info",
    )
    return redirect(url_for("collections.index"))
