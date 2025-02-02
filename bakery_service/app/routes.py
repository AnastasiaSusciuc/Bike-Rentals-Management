from flask import Blueprint, jsonify

auth_routes = Blueprint('auth', __name__)


@auth_routes.route('/login', methods=['POST'])
def login():
    # Authentication logic here
    return jsonify({"message": "Login successful"}), 200