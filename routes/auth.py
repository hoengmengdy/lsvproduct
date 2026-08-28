from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from extensions import db
from models import User, Cart, Order, Wishlist

auth_bp = Blueprint("auth", __name__)


def safe_next(target):
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target or ""))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated: return redirect(url_for("shop.home"))
    if request.method == "POST":
        name, email, password = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(password) < 8:
            flash("Enter a valid name, email, and password of at least 8 characters.", "danger")
        elif db.session.scalar(db.select(User).where(func.lower(User.email) == email)):
            flash("An account with that email already exists.", "warning")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            user.cart = Cart()
            db.session.add(user); db.session.commit(); login_user(user)
            flash("Welcome! Your account is ready.", "success")
            return redirect(url_for("shop.home"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: return redirect(url_for("shop.home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(db.select(User).where(func.lower(User.email) == email))
        if user and user.check_password(request.form.get("password", "")) and user.is_active:
            login_user(user, remember=bool(request.form.get("remember")))
            target = request.args.get("next")
            return redirect(target if target and safe_next(target) else url_for("shop.home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user(); flash("You have been signed out.", "info")
    return redirect(url_for("shop.home"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if len(name) < 2: flash("Name is too short.", "danger")
        else:
            current_user.name, current_user.phone, current_user.address = name, request.form.get("phone", "").strip(), request.form.get("address", "").strip()
            db.session.commit(); flash("Profile updated.", "success")
    return render_template("profile.html")


@auth_bp.get("/orders")
@login_required
def orders():
    orders = db.session.scalars(db.select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())).all()
    return render_template("orders.html", orders=orders)


@auth_bp.get("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    if order.user_id != current_user.id: return render_template("error.html", code=403, message="Access denied"), 403
    return render_template("order_detail.html", order=order)


@auth_bp.get("/wishlist")
@login_required
def wishlist():
    items = db.session.scalars(db.select(Wishlist).where(Wishlist.user_id == current_user.id).order_by(Wishlist.created_at.desc())).all()
    return render_template("wishlist.html", items=items)


@auth_bp.post("/wishlist/<int:product_id>/toggle")
@login_required
def toggle_wishlist(product_id):
    item = db.session.scalar(db.select(Wishlist).where(Wishlist.user_id == current_user.id, Wishlist.product_id == product_id))
    if item: db.session.delete(item); flash("Removed from wishlist.", "info")
    else: db.session.add(Wishlist(user_id=current_user.id, product_id=product_id)); flash("Added to wishlist.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("auth.wishlist"))
