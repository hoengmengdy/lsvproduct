import json
import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, or_

from extensions import db
from models import Admin, Category, Product

CATEGORIES = (("OKA", "oka"), ("RINs", "rins"), ("Empress", "empress"), ("NaturePlus", "natureplus"))
RETIRED_PRODUCT_NAMES = {"okalogo", "oka okalogo"}
RETIRED_PRODUCT_IMAGES = {"catalog-oka-07.webp"}

OLD_IMAGE_MIGRATIONS = {
    "oka-bright-3l.png": "catalog-oka-05.webp",
    "oka-refresh-3l.png": "catalog-oka-12.webp",
    "oka-zuper-3l.png": "catalog-oka-15.webp",
    "rins-lemongrass-1-2l.png": "catalog-rins-05.webp",
    "empress-orange-honey-800ml.png": "catalog-empress-03.webp",
    "empress-napa-peppermint-800ml.png": "catalog-empress-04.webp",
}


def ensure_catalog():
    """Add every packaged LSV product to a new or existing database."""
    manifest_path = Path(__file__).resolve().parent / "catalog_manifest.json"
    products = [
        item for item in json.loads(manifest_path.read_text(encoding="utf-8"))
        if item["name"].casefold() not in RETIRED_PRODUCT_NAMES
        and item["image"] not in RETIRED_PRODUCT_IMAGES
    ]
    by_image = {item["image"]: item for item in products}

    # Retire the mistakenly imported brand logo in existing databases as well.
    retired = db.session.scalars(db.select(Product).where(or_(
        func.lower(Product.name).in_(RETIRED_PRODUCT_NAMES),
        Product.image.in_(RETIRED_PRODUCT_IMAGES),
    ))).all()
    for product in retired:
        for cart_item in list(product.cart_items):
            db.session.delete(cart_item)
        if product.order_items:
            product.status = False
        else:
            db.session.delete(product)

    categories = {}
    for name, slug in CATEGORIES:
        category = db.session.scalar(db.select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(name=name, slug=slug)
            db.session.add(category)
        else:
            category.name = name
        categories[slug] = category
    db.session.flush()

    for old_image, new_image in OLD_IMAGE_MIGRATIONS.items():
        product = db.session.scalar(db.select(Product).where(Product.image == old_image))
        item = by_image[new_image]
        if product is not None:
            product.name = item["name"]
            product.description = item["description"]
            product.category = categories[item["category"]]
            product.image = new_image

    for item in products:
        product = db.session.scalar(db.select(Product).where(Product.image == item["image"]))
        if product is None:
            product = db.session.scalar(db.select(Product).where(Product.name == item["name"]))
        if product is None:
            product = Product(
                name=item["name"],
                description=item["description"],
                price=Decimal(item["price"]),
                old_price=Decimal(item["old_price"]) if item["old_price"] else None,
                stock=item["stock"],
                category=categories[item["category"]],
                image=item["image"],
                status=True,
            )
            db.session.add(product)
    db.session.commit()

def ensure_admin_from_env():
    """Provision or rotate the admin account without storing credentials in source."""
    username = (os.getenv("ADMIN_USERNAME") or "").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not username and not password:
        return
    if not username or len(password) < 10:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD (minimum 10 characters) must both be set.")
    admin = db.session.scalar(db.select(Admin).where(Admin.username == username))
    if admin is None:
        admin = Admin(username=username)
        db.session.add(admin)
    if not admin.password_hash or not admin.check_password(password):
        admin.set_password(password)
    db.session.commit()
