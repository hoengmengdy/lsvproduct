from extensions import db


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(db.Model):
    __table_args__ = (db.UniqueConstraint("cart_id", "product_id"),)
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", back_populates="cart_items")

