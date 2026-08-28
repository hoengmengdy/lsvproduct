from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Cart, Order, OrderItem
from services.payments import get_payment_provider

checkout_bp = Blueprint("checkout", __name__)


@checkout_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = db.session.scalar(db.select(Cart).where(Cart.user_id == current_user.id))
    if not cart or not cart.items:
        flash("Your cart is empty.", "warning"); return redirect(url_for("cart.view_cart"))
    subtotal = sum((item.product.price * item.quantity for item in cart.items), Decimal("0"))
    delivery_fee = Decimal("1.50")
    total = subtotal + delivery_fee
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        province = request.form.get("province", "").strip()
        address, phone, method = request.form.get("address", "").strip(), request.form.get("phone", "").strip(), request.form.get("payment_method", "")
        if not name or not province or not address or not phone or method not in {"cod", "khqr"}: flash("Complete all checkout fields.", "danger")
        elif any(i.quantity > i.product.stock or not i.product.status for i in cart.items): flash("One or more products are no longer available.", "danger")
        else:
            current_user.name, current_user.phone, current_user.address = name, phone, address
            order = Order(user_id=current_user.id, total_amount=total, payment_method=method, shipping_address=f"{province} — {address}", phone=phone, payment_status="pending")
            for item in list(cart.items):
                order.items.append(OrderItem(product_id=item.product.id, product_name=item.product.name, price=item.product.price, quantity=item.quantity))
                item.product.stock -= item.quantity; db.session.delete(item)
            db.session.add(order); db.session.flush()
            payment = get_payment_provider(method).initialize(order)
            order.payment_status = payment["status"]
            db.session.commit()
            flash("Order confirmed. Payment is pending.", "success")
            return redirect(url_for("auth.order_detail", order_id=order.id))
    return render_template("checkout.html", cart=cart, subtotal=subtotal, delivery_fee=delivery_fee, total=total)
