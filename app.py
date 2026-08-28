from pathlib import Path
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from dotenv import load_dotenv

load_dotenv()

from config import Config
from extensions import db, login_manager, csrf
from models import User, Cart, Category
from translations import translate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    if not app.config.get("IS_VERCEL"):
        (Path(app.root_path) / "database").mkdir(exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from routes.auth import auth_bp
    from routes.shop import shop_bp
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(admin_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def global_context():
        count = 0
        if current_user.is_authenticated:
            cart = db.session.scalar(db.select(Cart).where(Cart.user_id == current_user.id))
            count = sum(item.quantity for item in cart.items) if cart else 0
        nav_categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
        lang = session.get("lang", "km")
        return {"cart_count": count, "nav_categories": nav_categories, "lang": lang, "t": lambda key, default=None: translate(lang, key, default)}

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(413)
    def too_large(error):
        return render_template("error.html", code=413, message="Uploaded file is too large"), 413

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template("error.html", code=405, message="??????????????????????????? ???????????????????????"), 405

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        flash("????????????????? ??????????????????", "warning")
        if request.endpoint == "cart.add" and not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.referrer or url_for("shop.shop")))
        return redirect(request.referrer or url_for("shop.home"))

    with app.app_context():
        db.create_all()
        if config_class is Config:
            from bootstrap_catalog import ensure_catalog
            ensure_catalog()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)


