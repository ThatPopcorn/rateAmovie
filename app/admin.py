# app/admin.py
import secrets
import time
import os
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from .extensions import db

# TODO:
# - Implement stricter validation and command whitelisting for SQL execution
# - Add a better authentication mechanism for admin access (e.g. OAuth, multi-factor auth, administrator access to accounts)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/hidden/v1')

admin_state = { "token": None, "expires_at": 0 }

# Byron: This is a simple logging mechanism to keep track of executed SQL commands and their results.
def submit_to_logs(command, result):
    """Submit executed command and result to logs (for auditing)"""
    log_entry = f"{time.ctime()}: Executed SQL: {command} | Result: {result}\n"
    with open("admin_sql_logs.txt", "a") as log_file:
        log_file.write(log_entry)

# Byron: This is a temporary method to generate an admin token. In a production environment, 
# I will implement a more secure and robust authentication mechanism for administrators.
# Essentially creates a token that will not be stored anywhere except admin_state, stored in memory.
def generate_admin_token():
    """Generate a temporary admin token valid for 1 hour"""
    token = secrets.token_urlsafe(32)
    admin_state["token"] = token
    admin_state["expires_at"] = time.time() + 3600
    print(f"\n Administrator session key: {token}")
    print(f" Valid until: {time.ctime(admin_state['expires_at'])}\n")
    return token

# Byron: This is a dangerous method, I will keep it protected and later implement
# an actual guideline for allowed commands so someone doesnt mess up the database.
@admin_bp.route('/exec', methods=['POST'])
def execute_sql():
    """Execute raw SQL command (SELECT, INSERT, UPDATE, DELETE)"""
    request_token = request.headers.get('X-Admin-Auth')
    
    # Byron: This is probably not the most secure way to handle admin auth, but it's sufficient for now
    # as this endpoint is hidden and wont be exposed publicly. In a production environment, I will consider using
    # a more robust authentication mechanism. Admin tokens are only showed serverside.
    if not admin_state["token"] or request_token != admin_state["token"]:
        return jsonify({"error": "Not Found"}), 404
    
    # Byron: This is fine...
    if time.time() > admin_state["expires_at"]:
        return jsonify({"error": "Session expired"}), 403

    try:
        data = request.get_json()
        sql_command = data.get('sql', '').strip()
        result = db.session.execute(text(sql_command))
        
        if sql_command.upper().startswith("SELECT"):
            keys = result.keys()
            data = [dict(zip(keys, row)) for row in result]
            submit_to_logs(sql_command, data)
            return jsonify({"status": "success", "data": data})
        else:
            db.session.commit()
            submit_to_logs(sql_command, "Executed without SELECT")
            return jsonify({"status": "success", "message": "Executed."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Byron: Invalidates the current admin token and logs it.
@admin_bp.route('/logout', methods=['POST'])
def logout():
    """End admin session"""
    global admin_state
    admin_state["token"] = None
    admin_state["expires_at"] = 0
    submit_to_logs("Admin Logout", "Admin session ended")
    return jsonify({"status": "success", "message": "Logged out"}), 200