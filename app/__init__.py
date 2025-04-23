from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # Import Flask-Migrate
from .models import db, bcrypt, User  # Import User model
from jinja2 import Environment
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "enter your sql lite secret key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

    db.init_app(app)
    bcrypt.init_app(app)
    
    migrate = Migrate(app, db)  # Add this line to initialize Flask-Migrate

    login_manager = LoginManager()
    login_manager.login_view = "routes.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Fetch user from DB

    from .routes import routes_bp
    app.register_blueprint(routes_bp)
    @app.template_filter('intcomma')
    def intcomma_filter(value):
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            return value

    return app



