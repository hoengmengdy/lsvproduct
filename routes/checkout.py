from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from extensions import db
from models import Cart, Order, OrderItem, ShippingAddress
from services.payments import get_payment_provider
from services.addresses import address_values, serialize_address

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
    addresses = db.session.scalars(db.select(ShippingAddress).where(ShippingAddress.user_id == current_user.id)
                                   .order_by(ShippingAddress.is_default.desc(), ShippingAddress.id.desc())).all()
    selected_id = request.form.get("address_id", type=int) if request.method == "POST" else (request.args.get("address", type=int) or (addresses[0].id if addresses else None))
    if request.method == "POST":
        address = next((a for a in addresses if a.id == selected_id), None)
        method = request.form.get("payment_method", "")
        if address is None or method != "khqr": flash("Choose a delivery address and payment method.", "danger")
        elif any(i.quantity > i.product.stock or not i.product.status for i in cart.items): flash("One or more products are no longer available.", "danger")
        else:
            shipping = serialize_address(address, session.get("lang", "km"))
            order = Order(user_id=current_user.id, total_amount=total, payment_method=method,
                          shipping_address=shipping["name"] + " - " + shipping["formatted"],
                          phone=address.phone, payment_status="pending")
            for item in list(cart.items):
                order.items.append(OrderItem(product_id=item.product.id, product_name=item.product.name, price=item.product.price, quantity=item.quantity))
                item.product.stock -= item.quantity; db.session.delete(item)
            db.session.add(order); db.session.flush()
            payment = get_payment_provider(method).initialize(order)
            order.payment_status = payment["status"]
            db.session.commit()
            flash("Order confirmed. Payment is pending.", "success")
            return redirect(url_for("auth.order_detail", order_id=order.id))
    return render_template("checkout.html", cart=cart, subtotal=subtotal, delivery_fee=delivery_fee, total=total,
                           addresses=[serialize_address(a, session.get("lang", "km")) for a in addresses], selected_id=selected_id)


@checkout_bp.post("/checkout/addresses")
@login_required
def save_address():
    try:
        values = address_values(request.form)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    raw_id = request.form.get("address_id", "").strip()
    address_id = request.form.get("address_id", type=int)
    if raw_id and address_id is None:
        return jsonify(error="Address not found."), 404
    if raw_id:
        address = db.session.scalar(db.select(ShippingAddress).where(
            ShippingAddress.id == address_id, ShippingAddress.user_id == current_user.id))
        if address is None:
            return jsonify(error="Address not found."), 404
    else:
        address = ShippingAddress(user_id=current_user.id)
    if values["is_default"]:
        for saved in db.session.scalars(db.select(ShippingAddress).where(ShippingAddress.user_id == current_user.id)):
            saved.is_default = False
    for key, value in values.items():
        setattr(address, key, value)
    db.session.add(address)
    if address.is_default:
        current_user.phone = address.phone
        current_user.address = serialize_address(address, session.get("lang", "km"))["formatted"]
    db.session.commit()
    return jsonify(address=serialize_address(address, session.get("lang", "km")))
