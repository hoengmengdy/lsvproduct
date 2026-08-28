from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    cart = db.relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self.is_active_user

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)


class Wishlist(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "product_id"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlisted_by")

