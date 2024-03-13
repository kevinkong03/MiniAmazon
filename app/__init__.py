from flask import Flask
from flask_login import LoginManager
from .config import Config
from .db import DB


login = LoginManager()
login.login_view = 'users.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)

    from .index import bp as index_bp
    app.register_blueprint(index_bp)

    from .users import bp as user_bp
    app.register_blueprint(user_bp)

    from .cart import bp as cart_bp 
    app.register_blueprint(cart_bp)

    from .inventory import bp as inventory_bp 
    app.register_blueprint(inventory_bp)

    from .order import bp as orders_bp
    app.register_blueprint(orders_bp)

    from .reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp)

    from .account import bp as account_bp 
    app.register_blueprint(account_bp)

    from .productView import bp as productView_bp
    app.register_blueprint(productView_bp)

    from .write_reviews import bp as write_reviews_bp
    app.register_blueprint(write_reviews_bp)

    from .write_product_reviews import bp as write_product_reviews_bp
    app.register_blueprint(write_product_reviews_bp)

    from .edit_review import bp as edit_review_bp
    app.register_blueprint(edit_review_bp)

    from .edit_seller_review import bp as edit_seller_review_bp
    app.register_blueprint(edit_seller_review_bp)
    from .wishlist import bp as wishlist_bp
    app.register_blueprint(wishlist_bp)

    return app
