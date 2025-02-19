import queue
import random

from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, Blueprint, request
from flask import current_app
from .broker import send_rental_request, send_return_request
from .models import db, User

from .utils import role_required
from .cache import rental_response_cache, return_response_cache

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = get_jwt_identity()

    claims = get_jwt()
    user = User.query.filter_by(username=claims.get('username'))

    if not user:
        user = User(
            role=claims.get('role'),
            name="Maria " + random.Random().randint(1, 1000).__str__(),
            username=claims.get('username')
        )
        db.session.add(user)
        db.session.commit()

    return jsonify({
        "id": user_id,
        "role": claims.get('role'),
        # "name": user.name,
        "username": claims.get('username')
    })


@user_bp.route('/rent', methods=['POST'])
def rent_bike():

    data = request.get_json()
    user_id = int(data.get('user_id'))
    bike_id = data.get('bike_id')

    if not user_id or not bike_id:
        return jsonify({"msg": "User ID and Bike ID are required"}), 400

    send_rental_request(user_id, bike_id)

    response = None
    attempts = 0
    while attempts < 10:
        try:
            response = rental_response_cache.get(timeout=2)
            break
        except queue.Empty:
            attempts += 1
            continue

    if not response:
        return jsonify({"msg": "Request timed out, please try again later."}), 408

    if response['status'] == 'success':
        return jsonify({"msg": response['message']}), 200
    elif response['status'] == 'failure':
        return jsonify({"msg": response['message']}), 400
    else:
        return jsonify({"msg": "An unexpected error occurred"}), 500


@user_bp.route('/return', methods=['POST'])
def return_bike():
    data = request.get_json()
    user_id = int(data.get('user_id'))
    bike_id = data.get('bike_id')

    current_app.logger.info(f"RETURN user_id {user_id} bike_id {bike_id}")

    if not user_id or not bike_id:
        return jsonify({"msg": "User ID and Bike ID are required"}), 400

    send_return_request(user_id, bike_id)

    response = None
    attempts = 0
    while attempts < 10:
        try:
            current_app.logger.info(f"ATTEMPTS {attempts}")
            response = return_response_cache.get(timeout=2)
            break
        except queue.Empty:
            attempts += 1
            continue

    if not response:
        return jsonify({"msg": "Request timed out, please try again later."}), 408

    if response['status'] == 'success':
        return jsonify({"msg": response['message']}), 200
    elif response['status'] == 'failure':
        return jsonify({"msg": response['message']}), 400
    else:
        return jsonify({"msg": "An unexpected error occurred"}), 500


@user_bp.route('/users', methods=['GET'])
@role_required('admin')
def get_all_users():
    users = User.query.all()

    if not users:
        return jsonify({"msg": "No users found"}), 200

    user_list = [
        {"id": user.id, "username": user.username, "name": user.name, "role": user.role}
        for user in users
    ]

    return jsonify({"users": user_list}), 200
