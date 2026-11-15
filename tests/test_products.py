from app.extensions import db
from app.models.product import Product
from app.models.collection import Collection


def test_add_product_success(app, auth_client_a, user_a):
    """Test adding a valid product to wishlist."""
    res = auth_client_a.post(
        "/products/new",
        data={
            "name": "Sony WH-1000XM5",
            "price": "26990.00",
            "collection_id": "0",
            "description": "Active noise cancelling headphones",
            "image_url": "https://images.example.com/sony.jpg",
            "purchase_url": "https://sony.co.in/buy",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"was added to your WishVault" in res.data

    with app.app_context():
        product = Product.query.filter_by(user_id=user_a.id, name="Sony WH-1000XM5").first()
        assert product is not None
        assert float(product.price) == 26990.00
        assert product.formatted_price == "₹26,990.00"
        assert product.is_purchased is False


def test_negative_and_zero_price_rejection(auth_client_a):
    """Input Validation: Negative and zero product prices must be rejected."""
    # Negative price
    res_neg = auth_client_a.post(
        "/products/new",
        data={"name": "Negative Item", "price": "-500.00", "collection_id": "0"},
        follow_redirects=True,
    )
    assert b"Price must be a positive amount" in res_neg.data

    # Zero price
    res_zero = auth_client_a.post(
        "/products/new",
        data={"name": "Zero Item", "price": "0.00", "collection_id": "0"},
        follow_redirects=True,
    )
    assert b"Price must be a positive amount" in res_zero.data


def test_dangerous_url_schemes_rejected(auth_client_a):
    """Input Validation: Reject dangerous URL schemes (javascript:, data:) in image and store links."""
    # Javascript scheme injection in purchase_url
    res_js = auth_client_a.post(
        "/products/new",
        data={
            "name": "XSS Item",
            "price": "100.00",
            "collection_id": "0",
            "purchase_url": "javascript:alert(document.cookie)",
        },
        follow_redirects=True,
    )
    assert b"Invalid store URL" in res_js.data

    # Data URI scheme in image_url
    res_data = auth_client_a.post(
        "/products/new",
        data={
            "name": "Data URI Item",
            "price": "100.00",
            "collection_id": "0",
            "image_url": "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        },
        follow_redirects=True,
    )
    assert b"Invalid image URL" in res_data.data


def test_search_and_filter_products(app, auth_client_a, user_a):
    """Test product search query and collection filtering."""
    with app.app_context():
        col_tech = Collection.query.filter_by(user_id=user_a.id, name="Electronics").first()
        col_fashion = Collection.query.filter_by(user_id=user_a.id, name="Fashion").first()
        col_tech_id = col_tech.id

        p1 = Product(user_id=user_a.id, collection_id=col_tech.id, name="Mechanical Keyboard", price=6500.00)
        p2 = Product(user_id=user_a.id, collection_id=col_fashion.id, name="Oversized Hoodie", price=2499.00)
        p3 = Product(user_id=user_a.id, collection_id=col_tech.id, name="Wireless Mouse", price=3200.00)
        db.session.add_all([p1, p2, p3])
        db.session.commit()

    # Search by keyword "Keyboard"
    res_search = auth_client_a.get("/products/?q=Keyboard")
    assert b"Mechanical Keyboard" in res_search.data
    assert b"Oversized Hoodie" not in res_search.data

    # Filter by Electronics collection
    res_filter = auth_client_a.get(f"/products/?collection={col_tech_id}")
    assert b"Mechanical Keyboard" in res_filter.data
    assert b"Wireless Mouse" in res_filter.data
    assert b"Oversized Hoodie" not in res_filter.data


def test_sort_products(app, auth_client_a, user_a):
    """Test sorting products by price low to high and high to low."""
    with app.app_context():
        p_cheap = Product(user_id=user_a.id, name="Cheapest Item", price=100.00)
        p_mid = Product(user_id=user_a.id, name="Mid Item", price=500.00)
        p_expensive = Product(user_id=user_a.id, name="Expensive Item", price=1000.00)
        db.session.add_all([p_cheap, p_mid, p_expensive])
        db.session.commit()

    res_asc = auth_client_a.get("/products/?sort=price_low")
    assert res_asc.status_code == 200
    # Cheapest should appear before Expensive in HTML
    idx_cheap = res_asc.data.find(b"Cheapest Item")
    idx_exp = res_asc.data.find(b"Expensive Item")
    assert idx_cheap < idx_exp

    res_desc = auth_client_a.get("/products/?sort=price_high")
    assert res_desc.status_code == 200
    idx_cheap_desc = res_desc.data.find(b"Cheapest Item")
    idx_exp_desc = res_desc.data.find(b"Expensive Item")
    assert idx_exp_desc < idx_cheap_desc
