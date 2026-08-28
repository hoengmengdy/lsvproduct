import unittest
from app import create_app
from extensions import db
from models import Admin, Category, Product, User, Order


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
        self.assertEqual(self.client.post("/checkout", data={"name": "Customer", "province": "Phnom Penh", "address": "123 Main Street", "phone": "012345678", "payment_method": "cod"}).status_code, 302)
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
