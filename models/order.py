from datetime import datetime, timezone
from extensions import db


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    payment_status = db.Column(db.String(30), default="pending", nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default="pending", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

