"""Import the shared LSV product image folders into the store catalog.

This script is idempotent: running it again updates matching image products
instead of creating duplicates. Prices and stock are starter values intended
to be adjusted from the admin dashboard.
"""
import re
import shutil
from hashlib import sha1
from pathlib import Path

from app import create_app
from extensions import db
from models import Category, Product

SOURCE_ROOT = Path(r"C:\Word\Lskkhmer\img")
BRANDS = {
    "oka": ("OKA", "oka"),
    "RINs": ("RINs", "rins"),
    "products Empress": ("Empress", "empress"),
}
ALLOWED = {".png", ".jpg", ".jpeg", ".webp"}
EMPRESS_PRICES = {
    "Empress Orange and Honey FA_Mockup": 3.75,
    "Empress_pineapple&honey-1000ml_FA": 2.50,
    "Mockup-Pineapple&Honey-800ml FA": 3.75,
    "Napa-Cabbage&Peppermint-800mlpng": 2.50,
    "Napa-cabbage-bodywashV2": 2.50,
    "Napa-Cabbage-foam120g": 2.50,
    "Neem&Turmeric-foam120g": 2.50,
    "New-Mockup-Box-face3": 2.50,
    "POUCH-refill-720ml-Mint-Cabbage": 2.00,
    "POUCH-refill-720ml-Rumdoul-Cabbage": 2.00,
    "POUCH-REFILL_Conditioner-435ml": 2.50,
    "POUCH-REFILL_Shampoo-450ml": 2.00,
    "Pouch-spout-60ml-Mint-Cabbage": 0.25,
    "Pouch-spout-60ml-Rumdoul-Cabbage": 0.25,
    "Pouch-spout-conditioner-30ml": 0.25,
    "Pouch-spout-shampoo-35ml": 0.25,
    "PouchCabbageNeem": 0.25,
    "Romdoul&Rice": 3.75,
    "Romdoul&spei-Mockup": 2.50,
    "Single-mockup": 2.50,
    "ក្រែមបន្ទន់សក់រូបរាងថ្មិ": 2.50,
    "ស្ពៃទឹកកថ្មី": 2.50,
    "ស្ពៃនិងស្ដៅ": 2.50,
    "ស្ពៃសរីរាង្គរូបរាងថ្មី": 2.50,
}


def display_name(stem):
    name = re.sub(r"(?i)(mock[- ]?up|front|copy|png|fa|ii|v2)", " ", stem)
    name = name.replace("_", " ").replace("&", " & ")
    name = re.sub(r"(?<=\d),(?=\d)", ".", name)
    name = re.sub(r"(?i)(\d)(ml|l)\b", r"\1 \2", name)
    name = re.sub(r"\s+", " ", name).strip(" -")
    return name.title()


def starter_price(name, brand):
    lower = name.lower()
    if "20l" in lower or "20 l" in lower: return 24.99
    if "10l" in lower or "10 l" in lower: return 14.99
    if "5l" in lower or "5 l" in lower: return 10.99
    if "3l" in lower or "3 l" in lower or "3.5l" in lower: return 7.99
    if "1.2l" in lower or "1.3l" in lower or "1000ml" in lower: return 4.99
    return 3.99 if brand == "Empress" else 4.49


app = create_app()
with app.app_context():
    upload_dir = Path(app.static_folder) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    imported = 0
    for folder, (brand, slug) in BRANDS.items():
        category = db.session.scalar(db.select(Category).where(Category.slug == slug))
        if not category:
            category = Category(name=brand, slug=slug)
            db.session.add(category); db.session.flush()
        for source in sorted((SOURCE_ROOT / folder).iterdir()):
            if not source.is_file() or source.suffix.lower() not in ALLOWED:
                continue
            digest = sha1(str(source).encode("utf-8")).hexdigest()[:10]
            target_name = f"{slug}-{digest}{source.suffix.lower()}"
            target = upload_dir / target_name
            if not target.exists() or target.stat().st_size != source.stat().st_size:
                shutil.copy2(source, target)
            product = db.session.scalar(db.select(Product).where(Product.image == target_name))
            if not product:
                clean_name = display_name(source.stem)
                product = Product(
                    name=f"{brand} {clean_name}",
                    description=f"Authentic {brand} product from LSV Industry. Update product details and pricing in the admin dashboard.",
                    price=starter_price(source.stem, brand),
                    stock=25,
                    category=category,
                    image=target_name,
                    status=True,
                )
                db.session.add(product)
                imported += 1
            if brand == "Empress" and source.stem in EMPRESS_PRICES:
                product.price = EMPRESS_PRICES[source.stem]
    db.session.commit()
    total = db.session.scalar(db.select(db.func.count(Product.id)))
    print(f"Imported {imported} new image products. Catalog now contains {total} products.")
