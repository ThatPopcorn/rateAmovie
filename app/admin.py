# app/admin.py
import secrets
import time
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from .extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/api/hidden/v1')

admin_state = { "token": None, "expires_at": 0 }

def generate_admin_token():
    token = secrets.token_urlsafe(32)
    admin_state["token"] = token
    admin_state["expires_at"] = time.time() + 3600
    print(f"\n Administrator session key: {token}")
    print(f" Valid until: {time.ctime(admin_state['expires_at'])}\n")

@admin_bp.route('/exec', methods=['POST'])
def execute_sql():
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