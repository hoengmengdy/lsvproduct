from flask import Blueprint, render_template, request, session, redirect
from sqlalchemy import or_
from extensions import db
from models import Product, Category

shop_bp = Blueprint("shop", __name__)


@shop_bp.post("/language/<lang>")
def set_language(lang):
    if lang in {"km", "en"}:
        session["lang"] = lang
    return redirect(request.referrer or "/")


@shop_bp.get("/")
def home():
    products = db.session.scalars(db.select(Product).where(Product.status.is_(True)).order_by(Product.created_at.desc()).limit(8)).all()
    featured = db.session.scalars(db.select(Product).where(Product.status.is_(True), Product.old_price.is_not(None)).limit(4)).all()
    if not featured:
        featured = db.session.scalars(db.select(Product).where(Product.status.is_(True)).order_by(Product.name).limit(4)).all()
    return render_template("index.html", products=products, featured=featured)


@shop_bp.get("/shop")
def shop():
    query = db.select(Product).where(Product.status.is_(True))
    q, category, sort = request.args.get("q", "").strip(), request.args.get("category", ""), request.args.get("sort", "newest")
    if q: query = query.where(or_(Product.name.ilike(f"%{q}%"), Product.description.ilike(f"%{q}%")))
    if category: query = query.join(Category).where(Category.slug == category)
    orders = {"price_asc": Product.price.asc(), "price_desc": Product.price.desc(), "name_asc": Product.name.asc(), "name_desc": Product.name.desc()}
    query = query.order_by(orders.get(sort, Product.created_at.desc()))
    products = db.session.scalars(query).all()
    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return render_template("shop.html", products=products, categories=categories, q=q, selected_category=category, sort=sort)


@shop_bp.get("/product/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    related = db.session.scalars(db.select(Product).where(Product.category_id == product.category_id, Product.id != product.id, Product.status.is_(True)).limit(4)).all()
    return render_template("product_detail.html", product=product, related=related)


@shop_bp.get("/api/products")
def products_api():
    products = db.session.scalars(db.select(Product).where(Product.status.is_(True))).all()
    return [{"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock, "category": p.category.name} for p in products]
