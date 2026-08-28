import getpass
from app import create_app
from extensions import db
from models import Admin, Category, Product

app = create_app()

SAMPLES = [
    ("Wireless Headphones", "Immersive sound, soft ear cushions, and all-day battery life.", 69.99, 89.99, 24, "electronics"),
    ("Smart Watch", "Track activity, notifications, heart rate, and daily wellness.", 119.00, 149.00, 16, "electronics"),
    ("Classic Backpack", "A durable everyday backpack with a padded laptop sleeve.", 45.00, None, 35, "fashion"),
    ("Minimal Sneakers", "Comfortable lightweight sneakers for work and weekends.", 59.50, 75.00, 28, "fashion"),
    ("Ceramic Table Lamp", "Warm ambient lighting with a clean sculptural silhouette.", 38.00, None, 20, "home"),
    ("Pour-over Coffee Set", "Everything needed for a balanced hand-brewed coffee.", 42.00, 55.00, 18, "home"),
]

with app.app_context():
    db.create_all()
    categories = {}
    for name, slug in [("Electronics", "electronics"), ("Fashion", "fashion"), ("Home & Living", "home")]:
        category = db.session.scalar(db.select(Category).where(Category.slug == slug)) or Category(name=name, slug=slug)
        db.session.add(category); categories[slug] = category
    db.session.flush()
    if not db.session.scalar(db.select(Product.id).limit(1)):
        for name, description, price, old_price, stock, slug in SAMPLES:
            db.session.add(Product(name=name, description=description, price=price, old_price=old_price, stock=stock, category=categories[slug]))
    db.session.commit()
    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password (min 10 characters): ")
    if not username or len(password) < 10: raise SystemExit("Username required and password must be at least 10 characters.")
    admin = db.session.scalar(db.select(Admin).where(Admin.username == username)) or Admin(username=username)
    admin.set_password(password); db.session.add(admin); db.session.commit()
    print("Database seeded and admin account saved securely.")

