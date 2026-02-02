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

    # JWT callback to check blacklist
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from .models import TokenBlacklist
        jti = jwt_payload.get('jti')
        blacklist_entry = TokenBlacklist.query.filter_by(jti=jti).first()
        return blacklist_entry is not None

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({"message": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import jsonify
        return jsonify({"message": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from flask import jsonify
        return jsonify({"message": "Request does not contain an access token"}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({"message": "Token has been revoked"}), 401

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