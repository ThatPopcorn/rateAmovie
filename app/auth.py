# app/auth.py
from flask import Blueprint, request, jsonify
from .extensions import db, limiter
from .models import User
from .config import Config
from flask_jwt_extended import create_access_token

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
        access_token = create_access_token(identity=user.id, expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES)
        return jsonify(access_token=access_token, username=user.username), 200

    return jsonify({"message": "Invalid credentials"}), 401