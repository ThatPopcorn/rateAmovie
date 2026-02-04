# app/auth.py
from flask import Blueprint, request, jsonify
from .extensions import db, limiter, jwt
from .models import User, TokenBlacklist
from .config import Config
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Byron: Checks username and email for uniqueness, tests password strength and later hashes it safely via bcrypt
@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({"message": "Username or Email already exists"}), 400
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Username or Email already exists"}), 400

    new_user = User(username=data.get('username'), email=data.get('email'))
    if not new_user.set_password(data.get('password')):
        return jsonify({"message": "Password strength must be greater"}), 400

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

# Byron: Checks credentials, creates access and refresh tokens with appropriate expiration times.
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        access_token = create_access_token(identity=str(user.id), expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
        refresh_token = create_refresh_token(identity=str(user.id), expires_delta=Config.JWT_REFRESH_TOKEN_EXPIRES)
        return jsonify(access_token=access_token, refresh_token=refresh_token, username=user.username, user_id=user.id), 200

    return jsonify({"message": "Invalid credentials"}), 401

# Byron: This endpoint allows users to refresh their access token using a valid refresh token. 
# Access tokens have a shorter lifespan for security, while refresh tokens can be used to obtain 
# new access tokens without requiring the user to log in again.
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id, expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
    return jsonify(access_token=access_token), 200

# Byron: This endpoint allows users to log out by adding their current access token to a blacklist.
# The blacklist is checked on every protected endpoint to ensure that revoked tokens cannot be used.
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout by adding token to blacklist"""
    claims = get_jwt()
    jti = claims.get('jti')
    
    if not jti:
        return jsonify({"message": "Could not identify token"}), 400
    
    # Add token to blacklist with expiration time
    expires_at = datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
    blacklist_entry = TokenBlacklist(jti=jti, expires_at=expires_at)
    db.session.add(blacklist_entry)
    db.session.commit()
    
    return jsonify({"message": "Successfully logged out"}), 200