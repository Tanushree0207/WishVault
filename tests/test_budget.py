from datetime import date
from app.extensions import db
from app.models.budget import Budget
from app.models.product import Product
from app.models.purchase import Purchase


def test_set_and_update_monthly_budget(app, auth_client_a, user_a):
    """Test setting and updating a monthly shopping budget."""
    today = date.today()

    res = auth_client_a.post(
        f"/budget/?year={today.year}&month={today.month}",
        data={
            "monthly_budget": "20000.00",
            "year": today.year,
            "month": today.month,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"set to" in res.data

    with app.app_context():
        budget = Budget.query.filter_by(
            user_id=user_a.id, year=today.year, month=today.month
        ).first()
        assert budget is not None
        assert float(budget.monthly_budget) == 20000.00
        assert budget.formatted_budget == "₹20,000.00"


def test_budget_80_percent_warning(app, auth_client_a, user_a):
    """Test budget manager displays 80% warning banner when spending is between 80% and 100%."""
    today = date.today()

    with app.app_context():
        # Set budget of 10,000 INR
        b = Budget(user_id=user_a.id, year=today.year, month=today.month, monthly_budget=10000.00)
        # Create product and purchase of 8,500 INR (85% of budget)
        p = Product(user_id=user_a.id, name="Test Phone", price=8500.00, is_purchased=True)
        db.session.add_all([b, p])
        db.session.flush()

        purchase = Purchase(
            user_id=user_a.id,
            product_id=p.id,
            purchase_date=today,
            actual_amount=8500.00,
        )
        db.session.add(purchase)
        db.session.commit()

    res = auth_client_a.get(f"/budget/?year={today.year}&month={today.month}")
    assert res.status_code == 200
    assert b"80% Threshold Warning" in res.data
    assert b"85.0%" in res.data


def test_budget_exceeded_alert(app, auth_client_a, user_a):
    """Test budget manager displays budget exceeded alert when spending exceeds 100%."""
    today = date.today()

    with app.app_context():
        # Budget 5,000 INR
        b = Budget(user_id=user_a.id, year=today.year, month=today.month, monthly_budget=5000.00)
        # Spending 6,500 INR (130% of budget)
        p = Product(user_id=user_a.id, name="Expensive Item", price=6500.00, is_purchased=True)
        db.session.add_all([b, p])
        db.session.flush()

        purchase = Purchase(
            user_id=user_a.id,
            product_id=p.id,
            purchase_date=today,
            actual_amount=6500.00,
        )
        db.session.add(purchase)
        db.session.commit()

    res = auth_client_a.get(f"/budget/?year={today.year}&month={today.month}")
    assert res.status_code == 200
    assert b"Budget Exceeded Alert" in res.data
    assert b"130.0%" in res.data


def test_negative_budget_rejected(auth_client_a):
    """Test setting a negative budget amount is rejected by server-side validator."""
    today = date.today()
    res = auth_client_a.post(
        f"/budget/?year={today.year}&month={today.month}",
        data={
            "monthly_budget": "-1000.00",
            "year": today.year,
            "month": today.month,
        },
        follow_redirects=True,
    )
    assert b"Budget must be 0 or a positive amount" in res.data
