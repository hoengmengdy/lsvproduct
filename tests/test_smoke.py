import unittest
from app import create_app
from extensions import db
from models import Admin, Category, Product, User, Order, OrderItem, Cart, CartItem, Wishlist


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-only"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = "static/uploads"


class StoreSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            category = Category(name="Test", slug="test")
            db.session.add(category); db.session.flush()
            db.session.add(Product(name="Test Product", description="A real product", price=10, old_price=12, stock=5, category_id=category.id))
            admin = Admin(username="admin"); admin.set_password("strong-test-password"); db.session.add(admin)
            db.session.commit()

    def test_store_and_order_flow(self):
        for path in ["/", "/shop", "/shop?q=Test&category=test&sort=price_asc", "/product/1", "/api/products", "/login", "/register", "/admin/login"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get("/cart/add/1").status_code, 302)
        response = self.client.post("/register", data={"name": "Customer", "email": "customer@example.com", "password": "password123"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post("/cart/add/1", data={"quantity": 2}).status_code, 302)
        for path in ["/cart", "/checkout", "/profile", "/orders", "/wishlist"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        checkout_page = self.client.get("/checkout").data
        self.assertNotIn(b'value="cod"', checkout_page)
        self.assertIn(b'value="khqr"', checkout_page)
        checkout_data = {"name": "Customer", "province": "Phnom Penh", "address": "123 Main Street", "phone": "012345678", "payment_method": "cod"}
        self.assertEqual(self.client.post("/checkout", data=checkout_data).status_code, 200)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(db.select(Order)))
            self.assertEqual(db.session.get(Product, 1).stock, 5)
        checkout_data["payment_method"] = "khqr"
        self.assertEqual(self.client.post("/checkout", data=checkout_data).status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(Order)).total_amount, 21.50)
            self.assertEqual(db.session.get(Product, 1).stock, 3)

    def test_admin_pages_and_updates(self):
        response = self.client.post("/admin/login", data={"username": "admin", "password": "strong-test-password"})
        self.assertEqual(response.status_code, 302)
        for path in ["/admin", "/admin/products", "/admin/products/add", "/admin/products/1/edit", "/admin/categories", "/admin/orders", "/admin/users"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        response = self.client.post("/admin/products/1/edit", data={"name": "Updated", "description": "Updated description", "price": "11.50", "stock": "7", "category_id": "1", "status": "on"})
        self.assertEqual(response.status_code, 302)

    def test_removed_logo_stays_removed_after_catalog_initialization(self):
        from bootstrap_catalog import ensure_catalog

        with self.app.app_context():
            logo = Product(name="okalogo", description="Brand logo", price=6.50,
                           stock=30, category_id=1, image="catalog-oka-07.webp")
            user = User(name="Customer", email="logo@example.com")
            user.set_password("password123")
            cart = Cart(user=user)
            cart.items.append(CartItem(product=logo, quantity=1))
            db.session.add_all([logo, user, cart, Wishlist(user=user, product=logo)])
            db.session.commit()
            logo_id = logo.id

            ensure_catalog()
            self.assertIsNone(db.session.scalar(db.select(Product).where(Product.name == "okalogo")))
            self.assertEqual(db.session.scalar(db.select(db.func.count(CartItem.id))), 0)
            self.assertEqual(db.session.scalar(db.select(db.func.count(Wishlist.id))), 0)
            count = db.session.scalar(db.select(db.func.count(Product.id)))
            ensure_catalog()
            self.assertEqual(db.session.scalar(db.select(db.func.count(Product.id))), count)
            self.assertIsNone(db.session.scalar(db.select(Product).where(Product.name == "okalogo")))
            self.assertEqual(db.session.get(Product, 1).name, "Test Product")

        self.assertNotIn(b"okalogo", self.client.get("/shop").data.lower())
        self.assertNotIn(b"okalogo", self.client.get("/api/products").data.lower())
        self.assertNotIn(b"okalogo", self.client.get(f"/product/{logo_id}").data.lower())

    def test_removed_logo_preserves_existing_order_history(self):
        from bootstrap_catalog import ensure_catalog

        with self.app.app_context():
            logo = Product(name="Renamed logo", description="Brand logo", price=6.50,
                           stock=30, category_id=1, image="catalog-oka-07.webp")
            user = User(name="Customer", email="history@example.com")
            user.set_password("password123")
            order = Order(user=user, total_amount=8, payment_method="khqr",
                          shipping_address="Test address", phone="012345678")
            order.items.append(OrderItem(product=logo, product_name="okalogo", price=6.50, quantity=1))
            db.session.add_all([logo, user, order])
            db.session.commit()
            logo_id, order_id = logo.id, order.id

            ensure_catalog()
            ensure_catalog()
            self.assertFalse(db.session.get(Product, logo_id).status)
            self.assertEqual(db.session.get(Order, order_id).items[0].product_name, "okalogo")
            self.assertEqual(db.session.get(Order, order_id).items[0].product_id, logo_id)

        self.assertNotIn(b"Renamed logo", self.client.get("/api/products").data)
        self.assertEqual(self.client.get(f"/product/{logo_id}").status_code, 404)

    def test_language_switcher(self):
        self.assertEqual(self.client.post("/language/en").status_code, 302)
        with self.client.session_transaction() as session:
            self.assertEqual(session["lang"], "en")
        self.assertIn(b"Featured products", self.client.get("/").data)

    def test_login_without_next_redirects_home(self):
        with self.app.app_context():
            user = User(name="Login User", email="login@example.com")
            user.set_password("password123")
            db.session.add(user); db.session.commit()
        response = self.client.post("/login", data={"email": "login@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")


if __name__ == "__main__":
    unittest.main()
