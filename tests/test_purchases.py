from datetime import date
from app.extensions import db
from app.models.product import Product
from app.models.purchase import Purchase


def test_mark_product_as_purchased(app, auth_client_a, user_a):
    """Test marking product as purchased creates purchase record and updates status."""
    with app.app_context():
        prod = Product(
            user_id=user_a.id,
            name="Air Jordan 1",
            price=12000.00,
            is_purchased=False,
        )
        db.session.add(prod)
        db.session.commit()
        prod_id = prod.id

    res = auth_client_a.post(
        f"/purchases/mark/{prod_id}",
        data={
            "actual_amount": "11500.00",
            "purchase_date": str(date.today()),
            "notes": "Bought on sale with card discount",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"was marked as purchased" in res.data

    with app.app_context():
        updated_prod = db.session.get(Product, prod_id)
        assert updated_prod.is_purchased is True
        purchase = Purchase.query.filter_by(product_id=prod_id).first()
        assert purchase is not None
        assert float(purchase.actual_amount) == 11500.00
        assert purchase.formatted_amount == "₹11,500.00"
        assert purchase.notes == "Bought on sale with card discount"


def test_undo_purchase(app, auth_client_a, user_a):
    """Test undoing accidental purchase restores product to wishlist and removes purchase record."""
    with app.app_context():
        prod = Product(
            user_id=user_a.id,
            name="Accidental Purchase Item",
            price=3000.00,
            is_purchased=True,
        )
        db.session.add(prod)
        db.session.flush()

        purchase = Purchase(
            user_id=user_a.id,
            product_id=prod.id,
            actual_amount=3000.00,
            purchase_date=date.today(),
        )
        db.session.add(purchase)
        db.session.commit()
        purchase_id = purchase.id
        prod_id = prod.id

    # Post undo request
    res = auth_client_a.post(f"/purchases/undo/{purchase_id}", follow_redirects=True)
    assert res.status_code == 200
    assert b"was undone. Item is restored to active wishlist" in res.data

    with app.app_context():
        updated_prod = db.session.get(Product, prod_id)
        assert updated_prod.is_purchased is False
        assert db.session.get(Purchase, purchase_id) is None


def test_purchase_tracker_list(app, auth_client_a, user_a):
    """Test shopping tracker page renders fulfilled purchases."""
    with app.app_context():
        prod = Product(user_id=user_a.id, name="Smart Bulb", price=999.00, is_purchased=True)
        db.session.add(prod)
        db.session.flush()
        purchase = Purchase(
            user_id=user_a.id,
            product_id=prod.id,
            actual_amount=899.00,
            purchase_date=date.today(),
            notes="Diwali offer",
        )
        db.session.add(purchase)
        db.session.commit()

    res = auth_client_a.get("/purchases/")
    assert res.status_code == 200
    assert b"Smart Bulb" in res.data
    assert b"899.00" in res.data
    assert b"Diwali offer" in res.data
