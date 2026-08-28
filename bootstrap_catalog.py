from decimal import Decimal

from extensions import db
from models import Category, Product

CATEGORIES = (("OKA", "oka"), ("RINs", "rins"), ("Empress", "empress"))
PRODUCTS = (
    ("OKA Bright 3L", "ទឹកសម្អាត និងបោកគក់ OKA Bright ចំណុះ 3 លីត្រ", "6.50", "7.50", 30, "oka", "oka-bright-3l.png"),
    ("OKA Refresh 3L", "ទឹកសម្អាត និងបោកគក់ OKA Refresh ចំណុះ 3 លីត្រ", "6.50", None, 30, "oka", "oka-refresh-3l.png"),
    ("OKA Zuper 3L", "ទឹកសម្អាត និងបោកគក់ OKA Zuper ចំណុះ 3 លីត្រ", "6.50", None, 30, "oka", "oka-zuper-3l.png"),
    ("RINs Lemongrass 1.2L", "សាប៊ូលាងចាន RINs ក្លិនស្លឹកគ្រៃ ចំណុះ 1.2 លីត្រ", "3.50", "4.00", 40, "rins", "rins-lemongrass-1-2l.png"),
    ("Empress Orange & Honey 800ml", "សាប៊ូកក់សក់ Empress ក្រូច និងទឹកឃ្មុំ ចំណុះ 800 មីលីលីត្រ", "3.75", None, 35, "empress", "empress-orange-honey-800ml.png"),
    ("Empress Napa Cabbage 800ml", "ផលិតផលថែរក្សាស្បែក Empress ស្ពៃបូកគោ និងជីរអង្កាម", "3.75", "4.25", 35, "empress", "empress-napa-peppermint-800ml.png"),
)


def ensure_catalog():
    """Create a production-safe starter catalog when a database is empty."""
    if db.session.scalar(db.select(Product.id).limit(1)):
        return
    categories = {}
    for name, slug in CATEGORIES:
        category = db.session.scalar(db.select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(name=name, slug=slug)
            db.session.add(category)
        categories[slug] = category
    db.session.flush()
    for name, description, price, old_price, stock, slug, image in PRODUCTS:
        db.session.add(Product(name=name, description=description, price=Decimal(price), old_price=Decimal(old_price) if old_price else None, stock=stock, category=categories[slug], image=image, status=True))
    db.session.commit()
