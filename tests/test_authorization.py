from app.extensions import db
from app.models.product import Product
from app.models.collection import Collection
from app.models.purchase import Purchase
from datetime import date


def test_user_a_cannot_view_user_b_product(app, auth_client_a, user_b):
    """IDOR Test: User A attempts to view User B's product detail (must return 403 Forbidden)."""
    with app.app_context():
        b_prod = Product(
            user_id=user_b.id,
            name="Confidential Item B",
            price=9999.00,
        )
        db.session.add(b_prod)
        db.session.commit()
        b_prod_id = b_prod.id

    res = auth_client_a.get(f"/products/{b_prod_id}")
    assert res.status_code == 403
    assert b"Access Forbidden" in res.data


def test_user_a_cannot_edit_user_b_product(app, auth_client_a, user_b):
    """IDOR Test: User A attempts to edit User B's product (must return 403 Forbidden)."""
    with app.app_context():
        b_prod = Product(
            user_id=user_b.id,
            name="Original Item B",
            price=5000.00,
        )
        db.session.add(b_prod)
        db.session.commit()
        b_prod_id = b_prod.id

    res = auth_client_a.post(
        f"/products/{b_prod_id}/edit",
        data={"name": "Hacked by User A", "price": 10.00},
    )
    assert res.status_code == 403

    # Verify database was NOT changed
    with app.app_context():
        prod = db.session.get(Product, b_prod_id)
        assert prod.name == "Original Item B"
        assert float(prod.price) == 5000.00


def test_user_a_cannot_delete_user_b_product(app, auth_client_a, user_b):
    """IDOR Test: User A attempts to delete User B's product (must return 403 Forbidden)."""
    with app.app_context():
        b_prod = Product(
            user_id=user_b.id,
            name="Undeletable Item B",
            price=3000.00,
        )
        db.session.add(b_prod)
        db.session.commit()
        b_prod_id = b_prod.id

    res = auth_client_a.post(f"/products/{b_prod_id}/delete")
    assert res.status_code == 403

    # Verify product still exists in DB
    with app.app_context():
        assert db.session.get(Product, b_prod_id) is not None


def test_user_a_cannot_view_or_edit_user_b_collection(app, auth_client_a, user_b):
    """IDOR Test: User A cannot view, edit or delete User B's collection."""
    with app.app_context():
        b_col = Collection(
            user_id=user_b.id,
            name="Beta Private Collection",
            icon="sparkles",
            color="lavender",
        )
        db.session.add(b_col)
        db.session.commit()
        b_col_id = b_col.id

    # View attempt
    res_view = auth_client_a.get(f"/collections/{b_col_id}")
    assert res_view.status_code == 403

    # Edit attempt
    res_edit = auth_client_a.post(
        f"/collections/{b_col_id}/edit",
        data={"name": "Hacked Collection", "icon": "shirt", "color": "rose"},
    )
    assert res_edit.status_code == 403

    # Delete attempt
    res_del = auth_client_a.post(f"/collections/{b_col_id}/delete")
    assert res_del.status_code == 403

    # Verify collection untouched
    with app.app_context():
        assert db.session.get(Collection, b_col_id) is not None


def test_user_a_cannot_mark_user_b_product_purchased(app, auth_client_a, user_b):
    """IDOR Test: User A cannot mark User B's product as purchased."""
    with app.app_context():
        b_prod = Product(
            user_id=user_b.id,
            name="Unpurchased Item B",
            price=2500.00,
            is_purchased=False,
        )
        db.session.add(b_prod)
        db.session.commit()
        b_prod_id = b_prod.id

    res = auth_client_a.post(
        f"/purchases/mark/{b_prod_id}",
        data={"actual_amount": 2500.00, "purchase_date": str(date.today())},
    )
    assert res.status_code == 403

    with app.app_context():
        prod = db.session.get(Product, b_prod_id)
        assert prod.is_purchased is False


def test_user_a_cannot_undo_user_b_purchase(app, auth_client_a, user_b):
    """IDOR Test: User A cannot undo User B's purchase record."""
    with app.app_context():
        b_prod = Product(
            user_id=user_b.id,
            name="Purchased Item B",
            price=4000.00,
            is_purchased=True,
        )
        db.session.add(b_prod)
        db.session.flush()

        b_purchase = Purchase(
            user_id=user_b.id,
            product_id=b_prod.id,
            purchase_date=date.today(),
            actual_amount=4000.00,
        )
        db.session.add(b_purchase)
        db.session.commit()
        b_purchase_id = b_purchase.id

    res = auth_client_a.post(f"/purchases/undo/{b_purchase_id}")
    assert res.status_code == 403

    with app.app_context():
        assert db.session.get(Purchase, b_purchase_id) is not None


def test_wishlist_isolation(app, auth_client_a, user_a, user_b):
    """Verify User A's wishlist index contains only User A's products, never User B's."""
    with app.app_context():
        prod_a = Product(user_id=user_a.id, name="User A Laptop", price=50000.00)
        prod_b = Product(user_id=user_b.id, name="User B Secret", price=75000.00)
        db.session.add_all([prod_a, prod_b])
        db.session.commit()

    res = auth_client_a.get("/products/")
    assert res.status_code == 200
    assert b"User A Laptop" in res.data
    assert b"User B Secret" not in res.data
