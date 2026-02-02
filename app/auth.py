# app/auth.py
from flask import Blueprint, request, jsonify
from .extensions import db, limiter, jwt
from .models import User, TokenBlacklist
from .config import Config
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({"message": "Username already exists"}), 400
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Email already exists"}), 400

    new_user = User(username=data.get('username'), email=data.get('email'))
    new_user.set_password(data.get('password'))

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        access_token = create_access_token(identity=str(user.id), expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
        refresh_token = create_refresh_token(identity=str(user.id), expires_delta=Config.JWT_REFRESH_TOKEN_EXPIRES)
        return jsonify(access_token=access_token, refresh_token=refresh_token, username=user.username), 200

    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id, expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
    return jsonify(access_token=access_token), 200

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