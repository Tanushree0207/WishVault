import os
from app import create_app
from app.utils.sample_data import seed_sample_data

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)


@app.cli.command("seed-db")
def seed_db():
    """Command-line utility to seed demo data."""
    seed_sample_data(app)
    print("✓ Successfully seeded demo data!")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
    print("=" * 60)
    print("🌸 WishVault – Personal Shopping & Wishlist Manager")
    print("   'Your wishes, beautifully organized.'")
    print(f"   Environment: {env.title()} | Debug: {debug}")
    print(f"   Running on: http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host="127.0.0.1", port=port, debug=debug)
