from functools import wraps
from pathlib import Path
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename
from extensions import db
from models import Admin, Product, Category, Order, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ORDER_STATUSES = {"pending", "confirmed", "processing", "shipped", "delivered", "cancelled"}
PAYMENT_STATUSES = {"pending", "paid", "failed", "refunded"}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def save_image(file):
    if not file or not file.filename: return None
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS: raise ValueError("Use PNG, JPG, WEBP, or GIF images.")
    filename = f"{uuid4().hex}.{ext}"
    file.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename)
    return filename


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"): return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        admin = db.session.scalar(db.select(Admin).where(Admin.username == request.form.get("username", "").strip()))
        if admin and admin.check_password(request.form.get("password", "")):
            session.clear(); session["admin_id"] = admin.id
            return redirect(url_for("admin.dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin/login.html")


@admin_bp.post("/logout")
def logout():
    session.pop("admin_id", None); return redirect(url_for("admin.login"))


@admin_bp.get("")
@admin_required
def dashboard():
    stats = {
        "products": db.session.scalar(db.select(func.count(Product.id))),
        "customers": db.session.scalar(db.select(func.count(User.id))),
        "orders": db.session.scalar(db.select(func.count(Order.id))),
        "revenue": db.session.scalar(db.select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.status != "cancelled")),
    }
    recent = db.session.scalars(db.select(Order).order_by(Order.created_at.desc()).limit(8)).all()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@admin_bp.get("/products")
@admin_required
def products():
    return render_template("admin/products.html", products=db.session.scalars(db.select(Product).order_by(Product.created_at.desc())).all())


def product_values(product):
    product.name = request.form.get("name", "").strip()
    product.description = request.form.get("description", "").strip()
    product.price = request.form.get("price", 0)
    product.old_price = request.form.get("old_price") or None
    product.stock = request.form.get("stock", 0)
    product.category_id = request.form.get("category_id", type=int)
    product.status = bool(request.form.get("status"))
    if not product.name or not product.description or float(product.price) < 0 or int(product.stock) < 0: raise ValueError("Enter valid product details.")
    image = save_image(request.files.get("image"))
    if image: product.image = image


@admin_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    product = Product()
    if request.method == "POST":
        try: product_values(product); db.session.add(product); db.session.commit(); flash("Product added.", "success"); return redirect(url_for("admin.products"))
        except (ValueError, TypeError): db.session.rollback(); flash("Could not save product. Check every field and image type.", "danger")
    return render_template("admin/product_form.html", product=product, categories=db.session.scalars(db.select(Category).order_by(Category.name)).all())


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        try: product_values(product); db.session.commit(); flash("Product updated.", "success"); return redirect(url_for("admin.products"))
        except (ValueError, TypeError): db.session.rollback(); flash("Could not save product. Check every field and image type.", "danger")
    return render_template("admin/product_form.html", product=product, categories=db.session.scalars(db.select(Category).order_by(Category.name)).all())


@admin_bp.post("/products/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    if product.order_items: product.status = False; flash("Product has order history, so it was archived.", "warning")
    else: db.session.delete(product); flash("Product deleted.", "info")
    db.session.commit(); return redirect(url_for("admin.products"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    if request.method == "POST":
        name, slug = request.form.get("name", "").strip(), request.form.get("slug", "").strip().lower()
        if not name or not slug: flash("Name and slug are required.", "danger")
        else:
            try: db.session.add(Category(name=name, slug=slug)); db.session.commit(); flash("Category added.", "success")
            except Exception: db.session.rollback(); flash("Category name and slug must be unique.", "danger")
    return render_template("admin/categories.html", categories=db.session.scalars(db.select(Category).order_by(Category.name)).all())


@admin_bp.post("/categories/<int:category_id>/delete")
@admin_required
def delete_category(category_id):
    category = db.get_or_404(Category, category_id)
    if category.products: flash("Move or delete its products first.", "warning")
    else: db.session.delete(category); db.session.commit(); flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.get("/orders")
@admin_required
def orders():
    return render_template("admin/orders.html", orders=db.session.scalars(db.select(Order).order_by(Order.created_at.desc())).all(), statuses=ORDER_STATUSES, payment_statuses=PAYMENT_STATUSES)


@admin_bp.post("/orders/<int:order_id>/status")
@admin_required
def order_status(order_id):
    order = db.get_or_404(Order, order_id)
    status, payment = request.form.get("status"), request.form.get("payment_status")
    if status in ORDER_STATUSES and payment in PAYMENT_STATUSES:
        order.status, order.payment_status = status, payment; db.session.commit(); flash("Order updated.", "success")
    else: flash("Invalid status.", "danger")
    return redirect(url_for("admin.orders"))


@admin_bp.get("/users")
@admin_required
def users():
    return render_template("admin/users.html", users=db.session.scalars(db.select(User).order_by(User.created_at.desc())).all())


@admin_bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id); user.is_active_user = not user.is_active_user; db.session.commit()
    flash("Customer status updated.", "success"); return redirect(url_for("admin.users"))

