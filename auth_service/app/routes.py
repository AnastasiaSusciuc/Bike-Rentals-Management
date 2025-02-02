import re
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from .models import User
from . import db
import datetime

auth_routes = Blueprint('auth', __name__)


@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', "renter")  # Default to "renter" if no role is provided

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    # Restrict username to letters and numbers only
    if not re.match("^[a-zA-Z0-9]+$", username):
        return jsonify({"message": "Username can only contain letters and numbers"}), 400

    if role not in ["renter", "admin"]:  # Limit roles to "renter" or "admin"
        return jsonify({"message": "Role must be 'renter' or 'admin'"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=datetime.timedelta(hours=1),
        additional_claims={
            "role": user.role,
            "username": user.username,
            "id": user.id,
        }
    )
    return jsonify({"message": "Login successful", "access_token": access_token}), 200
