# app/admin.py
import secrets
import time
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from .extensions import db
from .models import User

admin_bp = Blueprint('admin', __name__, url_prefix='/api/hidden/v1')

admin_state = { "token": None, "expires_at": 0 }

def generate_admin_token():
    token = secrets.token_urlsafe(32)
    admin_state["token"] = token
    admin_state["expires_at"] = time.time() + 3600
    print(f"\n Administrator session key: {token}")
    print(f" Valid until: {time.ctime(admin_state['expires_at'])}\n")
    return token

@admin_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and generate admin session token"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Authenticate user against the database
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate admin token
        token = generate_admin_token()
        expires_in = 3600  # 1 hour
        
        return jsonify({
            "status": "success",
            "message": f"Logged in as {username}",
            "token": token,
            "expires_in": expires_in,
            "user_id": user.id,
            "username": user.username
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@admin_bp.route('/exec', methods=['POST'])
def execute_sql():
    """Execute raw SQL command (SELECT, INSERT, UPDATE, DELETE)"""
    request_token = request.headers.get('X-Admin-Auth')
    
    if not admin_state["token"] or request_token != admin_state["token"]:
        return jsonify({"error": "Not Found"}), 404
    
    if time.time() > admin_state["expires_at"]:
        return jsonify({"error": "Session expired"}), 403

    try:
        data = request.get_json()
        sql_command = data.get('sql', '').strip()
        result = db.session.execute(text(sql_command))
        
        if sql_command.upper().startswith("SELECT"):
            keys = result.keys()
            data = [dict(zip(keys, row)) for row in result]
            return jsonify({"status": "success", "data": data})
        else:
            db.session.commit()
            return jsonify({"status": "success", "message": "Executed."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@admin_bp.route('/logout', methods=['POST'])
def logout():
    """End admin session"""
    global admin_state
    admin_state["token"] = None
    admin_state["expires_at"] = 0
    return jsonify({"status": "success", "message": "Logged out"}), 200