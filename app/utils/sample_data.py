from datetime import date, timedelta
from app.extensions import db
from app.models.user import User
from app.models.collection import Collection
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.budget import Budget

DEFAULT_COLLECTIONS = [
    {
        "name": "Fashion",
        "description": "Apparel, footwear, and curated wardrobe wishlist",
        "icon": "shirt",
        "color": "rose",
    },
    {
        "name": "Electronics",
        "description": "Gadgets, audio gear, and personal computing",
        "icon": "laptop",
        "color": "lavender",
    },
    {
        "name": "Beauty",
        "description": "Skincare, haircare, and wellness favorites",
        "icon": "heart",
        "color": "blush",
    },
    {
        "name": "Books",
        "description": "To-be-read list, personal growth, and fiction",
        "icon": "book",
        "color": "peach",
    },
    {
        "name": "Accessories",
        "description": "Watches, jewelry, bags, and daily essentials",
        "icon": "watch",
        "color": "mint",
    },
    {
        "name": "Home & Living",
        "description": "Cozy desk decor, aesthetic ceramics, and interior accents",
        "icon": "home",
        "color": "sky",
    },
    {
        "name": "Other",
        "description": "General items and miscellaneous wishlist finds",
        "icon": "tag",
        "color": "lavender",
    },
]


def create_default_collections_for_user(user: User) -> dict:
    """Create standard default collections for a user if they do not exist."""
    created = {}
    for col_data in DEFAULT_COLLECTIONS:
        existing = Collection.query.filter_by(
            user_id=user.id, name=col_data["name"]
        ).first()
        if not existing:
            col = Collection(
                user_id=user.id,
                name=col_data["name"],
                description=col_data["description"],
                icon=col_data["icon"],
                color=col_data["color"],
                is_default=True,
            )
            db.session.add(col)
            db.session.flush()
            created[col_data["name"]] = col
        else:
            created[col_data["name"]] = existing
    db.session.commit()
    return created


def seed_sample_data(app):
    """
    Seed realistic demonstration data for development/academic review.
    Creates demo user, collections, realistic INR products, purchases, and budget.
    """
    with app.app_context():
        demo_email = app.config.get("DEMO_EMAIL", "demo@wishvault.io")
        demo_password = app.config.get("DEMO_PASSWORD", "Demo@WishVault2026!")
        demo_name = app.config.get("DEMO_NAME", "Aarav Sharma")

        user = User.query.filter_by(email=demo_email).first()
        if not user:
            user = User(full_name=demo_name, email=demo_email)
            user.set_password(demo_password)
            db.session.add(user)
            db.session.commit()

        # Ensure default collections exist
        col_map = create_default_collections_for_user(user)

        # Check if products already seeded
        if Product.query.filter_by(user_id=user.id).count() == 0:
            sample_products = [
                {
                    "name": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
                    "collection": "Electronics",
                    "price": 26990.00,
                    "description": "Industry-leading active noise cancellation with 30-hour battery life and soft silver finish.",
                    "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.sony.co.in",
                    "purchased": False,
                },
                {
                    "name": "Nike Air Force 1 '07 Sneakers (Triple White)",
                    "collection": "Fashion",
                    "price": 8495.00,
                    "description": "Classic stitched overlays, crisp leather finish, and all-day cushioning.",
                    "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.nike.com/in",
                    "purchased": True,
                    "actual_paid": 7999.00,
                    "purchase_days_ago": 6,
                    "notes": "Bought during Nike end-of-season sale with 5% card discount.",
                },
                {
                    "name": "Laneige Lip Sleeping Mask (Berry 20g)",
                    "collection": "Beauty",
                    "price": 1250.00,
                    "description": "Enriched with Berry Fruit Complex, Vitamin C, and coconut oil for intensely soft lips overnight.",
                    "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.nykaa.com",
                    "purchased": True,
                    "actual_paid": 1200.00,
                    "purchase_days_ago": 12,
                    "notes": "Nykaa Super Saver bundle purchase.",
                },
                {
                    "name": "Apple Watch SE (GPS, 44mm Starlight Aluminum)",
                    "collection": "Accessories",
                    "price": 29900.00,
                    "description": "Heart rate notifications, Crash Detection, and enhanced workout tracking with Sport Loop.",
                    "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.apple.com/in",
                    "purchased": False,
                },
                {
                    "name": "Amazon Kindle Paperwhite (16 GB, 6.8\" Glare-Free)",
                    "collection": "Books",
                    "price": 14999.00,
                    "description": "Adjustable warm light, waterproof design, and weeks of battery life.",
                    "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.amazon.in",
                    "purchased": False,
                },
                {
                    "name": "Minimalist Pastel Vegan Leather Desk Mat (Lavender)",
                    "collection": "Home & Living",
                    "price": 1499.00,
                    "description": "Dual-sided waterproof aesthetic desk pad for keyboard, mouse and laptop setup.",
                    "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.amazon.in",
                    "purchased": True,
                    "actual_paid": 1349.00,
                    "purchase_days_ago": 3,
                    "notes": "Desk setup revamp item.",
                },
                {
                    "name": "Ceramic Artisan Coffee Mug with Cloud Saucer",
                    "collection": "Home & Living",
                    "price": 899.00,
                    "description": "Handcrafted aesthetic speckled ceramic cup with blush pink cloud saucer.",
                    "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&q=80",
                    "purchase_url": "https://www.amazon.in",
                    "purchased": False,
                },
            ]

            today = date.today()
            for item in sample_products:
                col = col_map.get(item["collection"])
                prod = Product(
                    user_id=user.id,
                    collection_id=col.id if col else None,
                    name=item["name"],
                    description=item["description"],
                    price=item["price"],
                    image_url=item["image_url"],
                    purchase_url=item["purchase_url"],
                    is_purchased=item["purchased"],
                )
                db.session.add(prod)
                db.session.flush()

                if item["purchased"]:
                    purchase_date = today - timedelta(
                        days=item.get("purchase_days_ago", 1)
                    )
                    purchase = Purchase(
                        user_id=user.id,
                        product_id=prod.id,
                        purchase_date=purchase_date,
                        actual_amount=item.get("actual_paid", item["price"]),
                        notes=item.get("notes"),
                    )
                    db.session.add(purchase)

            # Set monthly budget for current month (e.g. ₹15,000)
            # Total purchased so far in demo: 7999 + 1200 + 1349 = 10,548 INR
            # 10,548 / 15,000 = 70.3% of budget (ideal to show progress and near warning)
            current_budget = Budget.query.filter_by(
                user_id=user.id, year=today.year, month=today.month
            ).first()
            if not current_budget:
                current_budget = Budget(
                    user_id=user.id,
                    year=today.year,
                    month=today.month,
                    monthly_budget=15000.00,
                )
                db.session.add(current_budget)

            db.session.commit()
