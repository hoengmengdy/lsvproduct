from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Cart, CartItem, Product

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


def user_cart():
    cart = db.session.scalar(db.select(Cart).where(Cart.user_id == current_user.id))
    if not cart:
        cart = Cart(user_id=current_user.id); db.session.add(cart); db.session.commit()
    return cart


@cart_bp.get("")
@login_required
def view_cart():
    cart = user_cart()
    total = sum(item.product.price * item.quantity for item in cart.items)
    return render_template("cart.html", cart=cart, total=total)


@cart_bp.post("/add/<int:product_id>")
@login_required
def add(product_id):
    product = db.get_or_404(Product, product_id)
    try: quantity = max(1, int(request.form.get("quantity", 1)))
    except ValueError: quantity = 1
    cart = user_cart()
    item = db.session.scalar(db.select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product.id))
    wanted = quantity + (item.quantity if item else 0)
    if not product.status or product.stock < wanted:
        flash("Requested quantity is not available.", "danger")
    elif item: item.quantity = wanted; db.session.commit(); flash("Cart updated.", "success")
    else: db.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)); db.session.commit(); flash("Added to cart.", "success")
    return redirect(request.referrer or url_for("cart.view_cart"))


@cart_bp.get("/add/<int:product_id>")
def add_requires_post(product_id):
    """Handle login redirects or pasted add-to-cart URLs without a raw 405."""
    product = db.get_or_404(Product, product_id)
    flash("សូមចុចប៊ូតុង «ដាក់ចូលកន្ត្រក» ដើម្បីបន្ថែមផលិតផល។", "info")
    return redirect(url_for("shop.product_detail", product_id=product.id))


@cart_bp.post("/update/<int:item_id>")
@login_required
def update(item_id):
    item = db.get_or_404(CartItem, item_id)
    if item.cart.user_id != current_user.id: return ("Forbidden", 403)
    try: quantity = int(request.form.get("quantity", 1))
    except ValueError: quantity = 1
    if quantity <= 0: db.session.delete(item)
    elif quantity <= item.product.stock: item.quantity = quantity
    else: flash("Not enough stock.", "danger"); return redirect(url_for("cart.view_cart"))
    db.session.commit(); flash("Cart updated.", "success")
    return redirect(url_for("cart.view_cart"))


@cart_bp.post("/remove/<int:item_id>")
@login_required
def remove(item_id):
    item = db.get_or_404(CartItem, item_id)
    if item.cart.user_id != current_user.id: return ("Forbidden", 403)
    db.session.delete(item); db.session.commit(); flash("Item removed.", "info")
    return redirect(url_for("cart.view_cart"))
