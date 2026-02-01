# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import Config

# Import instances from extensions (Do NOT create new ones here)
from .extensions import db, bcrypt, jwt, ma, migrate, limiter

cors = CORS()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Import and register Blueprints
    from .auth import auth_bp
    from .routes import main_bp
    from .admin import admin_bp, generate_admin_token

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Create DB and Admin Token on startup
    with app.app_context():
        db.create_all()
        generate_admin_token()

    return app