import requests
from flask import Blueprint, request, jsonify
from .models import Bike, db, Rental
from .utils import role_required
import os

bike_bp = Blueprint('bike', __name__)

HOST_NAME = os.environ.get('HOST_NAME')


@bike_bp.route('/add', methods=['POST'])
@role_required('admin')
def add_bike():
    data = request.get_json()
    model = data.get('model')
    brand = data.get('brand')
    serial_number = data.get('serial_number')
    available_units = data.get('available_units', 1)

    if not model or not brand or not serial_number:
        return jsonify({"msg": "Model, brand, and serial number are required", "hostname": HOST_NAME}), 400

    # Ensure the serial number is unique
    existing_bike = Bike.query.filter_by(serial_number=serial_number).first()
    if existing_bike:
        return jsonify({"msg": "Bike with this serial number already exists", "hostname": HOST_NAME}), 400

    new_bike = Bike(model=model, brand=brand, serial_number=serial_number, available_units=available_units)
    print(os.path.abspath('bike_rentals.db'))
    print("NEW BIKE", new_bike)
    print("NEW BIKE", serial_number, available_units)
    db.session.add(new_bike)
    db.session.commit()
    return jsonify({"msg": "Bike added successfully", "hostname": HOST_NAME}), 201


@bike_bp.route('/all_bikes', methods=['GET'])
@role_required('admin', 'renter')
def get_all_bikes():
    try:
        bikes = Bike.query.all()

        if not bikes:
            return jsonify({"msg": "No bikes found", "hostname": HOST_NAME}), 404

        bike_list = [
            {
                "id": bike.id,
                "model": bike.model,
                "brand": bike.brand,
                "serial_number": bike.serial_number,
                "available_units": bike.available_units
            } for bike in bikes]

        return jsonify({"bikes": bike_list, "hostname": HOST_NAME}), 200

    except Exception as e:
        return jsonify({"msg": f"Error retrieving bikes: {str(e)}", "hostname": HOST_NAME}), 500


@bike_bp.route('/rented_bikes', methods=['GET'])
@role_required('admin', 'renter')
def get_rented_bikes():
    user_id = request.args.get('user_id')

    # Query the Rental table for bikes rented by this user
    # rentals = Rental.query.filter_by(user_id=user_id)
    rentals = Rental.query.filter(Rental.user_id == user_id).all()
    print("OSOSOS", os.path.abspath('bike_rentals.db'))
    if not rentals:
        return jsonify({"msg": "No bikes rented"}), 200

    rented_bikes = []
    for rental in rentals:
        bike = Bike.query.get(rental.bike_id)
        if bike:
            rented_bikes.append({
                "bike_id": bike.id,
                "model": bike.model,
                "brand": bike.brand,
                "serial_number": bike.serial_number,
                "return_by": rental.return_by,
                "returned_on": rental.returned_on
            })

    print(rented_bikes)
    return jsonify({
        "rented_bikes": rented_bikes,
        "hostname": os.getenv('HOST_NAME')
    }), 200


@bike_bp.route('/search', methods=['GET'])
@role_required('admin', 'renter')
def search_bike_by_model():
    model_query = request.args.get('model')

    if not model_query:
        return jsonify({"msg": "Model query parameter is required", "hostname": HOST_NAME}), 400

    # Perform a case-insensitive search for bikes with models that contain the query
    bikes = Bike.query.filter(Bike.model.ilike(f"%{model_query}%")).all()

    if not bikes:
        return jsonify({"msg": "No bikes found matching the model", "hostname": HOST_NAME}), 404

    # Format the result
    bike_list = [
        {
            "id": bike.id,
            "model": bike.model,
            "brand": bike.brand,
            "serial_number": bike.serial_number,
            "available_units": bike.available_units
        } for bike in bikes
    ]

    return jsonify({"bikes": bike_list, "hostname": HOST_NAME}), 200


@bike_bp.route('/search_by_brand', methods=['GET'])
@role_required('admin', 'renter')
def search_bike_by_brand():
    brand_query = request.args.get('brand')

    if not brand_query:
        return jsonify({"msg": "Brand query parameter is required", "hostname": HOST_NAME}), 400

    # Perform a case-insensitive search for bikes with brands that contain the query
    bikes = Bike.query.filter(Bike.brand.ilike(f"%{brand_query}%")).all()

    if not bikes:
        return jsonify({"msg": "No bikes found matching the brand", "hostname": HOST_NAME}), 404

    # Format the result
    bike_list = [
        {
            "id": bike.id,
            "model": bike.model,
            "brand": bike.brand,
            "serial_number": bike.serial_number,
            "available_units": bike.available_units
        } for bike in bikes
    ]

    return jsonify({"bikes": bike_list, "hostname": HOST_NAME}), 200


@bike_bp.route('/get-garages', methods=['GET'])
def get_garages():
    bikes_count = Bike.query.count()
    response = requests.post(os.getenv('LAMBDA_URL'), json={"bikes": bikes_count})

    if response.status_code == 200:
        response_data = response.json()
        return jsonify(response_data)
    else:
        return jsonify({"error": "Error calling Lambda function"}), 500
