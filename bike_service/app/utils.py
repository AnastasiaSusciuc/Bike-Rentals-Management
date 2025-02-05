from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required

import requests
import json


def call_lambda_for_garages(bikes_count):
    # Define the Lambda URL
    lambda_url = "https://bag4vefhr6dqmlslq6cvoi4c2u0hrxko.lambda-url.eu-north-1.on.aws/"

    # Prepare the payload data
    payload = {"bikes": bikes_count}

    # Make a POST request to the Lambda function
    response = requests.post(lambda_url, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        # Parse and print the response from Lambda
        response_data = response.json()
        print(f"Number of bikes: {response_data['number bikes']}")
        print(f"Garages needed: {response_data['garages']}")
    else:
        # Handle errors
        print(f"Error calling Lambda function: {response.status_code}")
        print(response.text)


# # Example usage
# bikes_count = 28
# call_lambda_for_garages(bikes_count)


def role_required(*roles):
    """
    Decorator to check if the user has one of the required roles.
    :param roles: One or more roles ('admin', 'biker') that are allowed to access the route.
    """

    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            # current_app.logger.debug(f"JWT Claims: {claims}")
            if claims.get('role') not in roles:
                return jsonify(
                    {"msg": f"Access denied: One of the following roles is required: {', '.join(roles)}"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator
