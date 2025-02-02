import pika
import json
from flask import current_app
from models import Bike, Rental, db, WaitingList
from datetime import datetime, timedelta
from kafka import KafkaProducer
import logging

logging.getLogger("pika").setLevel(logging.INFO)

###########################
# KAFKA PRODUCER SETUP
###########################

producer = KafkaProducer(
    bootstrap_servers='kafka1:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def publish_rental_request(bike_id, user_id):
    """Publishes a rental request to Kafka when a bike is unavailable."""
    event = {
        "bike_id": bike_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.send('rental-requests', event)
    current_app.logger.info(f"Published rental request to Kafka: {event}")


def notify_user_bike_available(user_id, bike_id):
    """Notify the user that a bike is available."""
    event = {
        "user_id": user_id,
        "bike_id": bike_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.send('bike-availability', event)
    current_app.logger.info(f"Published bike availability notification for User {user_id} and Bike {bike_id}")


###########################
# RENT BIKE
###########################

def on_rent_bike_message(ch, method, properties, body):
    with current_app.app_context():
        message = json.loads(body)
        user_id = message.get('user_id')
        bike_id = message.get('bike_id')

        current_app.logger.info(f"Received rental request from user {user_id} for bike {bike_id}")

        response = {'user_id': user_id, 'bike_id': bike_id, 'status': 'failure', 'message': ''}

        try:
            bike = Bike.query.get(bike_id)
            if not bike:
                response['message'] = f"Bike with ID {bike_id} not found."
                current_app.logger.error(response['message'])
            elif bike.available_units <= 0:
                response['message'] = f"No bikes available for ID {bike_id}. Added to waiting list."
                current_app.logger.warning(response['message'])

                waiting_list_entry = WaitingList(bike_id=bike.id, user_id=user_id)
                db.session.add(waiting_list_entry)
                db.session.commit()
            else:
                existing_rental = Rental.query.filter_by(user_id=user_id, bike_id=bike_id, returned_on=None).first()
                if existing_rental:
                    response['message'] = f"User {user_id} has already rented bike {bike_id}."
                    current_app.logger.warning(response['message'])
                else:
                    return_by = datetime.utcnow() + timedelta(days=3)  # Set rental return date
                    rental = Rental(bike_id=bike.id, user_id=user_id, return_by=return_by)

                    bike.available_units -= 1
                    db.session.add(rental)
                    db.session.commit()

                    response['status'] = 'success'
                    response['message'] = f"Bike rented successfully for user {user_id}."
                    current_app.logger.info(response['message'])

        except Exception as e:
            response['message'] = f"Error processing rental request: {str(e)}"
            current_app.logger.error(response['message'])

        send_rental_response(response)
        ch.basic_ack(delivery_tag=method.delivery_tag)


def send_rental_response(response):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='rental_response_queue', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='rental_response_queue',
            body=json.dumps(response),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        current_app.logger.info(f"Sent rental response: {response}")
        connection.close()
    except Exception as e:
        current_app.logger.error(f"Error sending rental response: {str(e)}")


def start_rental_request_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='rental_request_queue', durable=True)
        channel.basic_consume(queue='rental_request_queue', on_message_callback=on_rent_bike_message)
        current_app.logger.info("Started listening for rental requests...")
        channel.start_consuming()
    except Exception as e:
        current_app.logger.error(f"Error in consuming rental messages: {str(e)}")


###########################
# RETURN BIKE
###########################

def send_return_response(user_id, bike_id, status, message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='return_response_queue', durable=True)
        response_message = json.dumps({"user_id": user_id, "bike_id": bike_id, "status": status, "message": message})
        channel.basic_publish(
            exchange='',
            routing_key='return_response_queue',
            body=response_message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
    except Exception as e:
        current_app.logger.error(f"Error sending return response: {str(e)}")


def on_return_request(ch, method, properties, body):
    try:
        request_data = json.loads(body)
        user_id = request_data['user_id']
        bike_id = request_data['bike_id']

        rental = Rental.query.filter_by(user_id=user_id, bike_id=bike_id, returned_on=None).first()
        if not rental:
            send_return_response(user_id, bike_id, 'failure', 'Bike not found or not rented')
        else:
            rental.returned_on = datetime.utcnow()
            db.session.commit()

            bike = Bike.query.get(bike_id)
            if bike:
                bike.available_units += 1
                db.session.commit()
                waiting_list = WaitingList.query.filter_by(bike_id=bike_id).all()
                if waiting_list:
                    for entry in waiting_list:
                        notify_user_bike_available(entry.user_id, bike_id)
                    WaitingList.query.filter_by(bike_id=bike_id).delete()
                    db.session.commit()
            send_return_response(user_id, bike_id, 'success', f'Bike {bike_id} returned successfully')
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        send_return_response(user_id, bike_id, 'failure', f'Error processing return request: {str(e)}')


def start_return_request_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='return_request_queue', durable=True)
        channel.basic_consume(queue='return_request_queue', on_message_callback=on_return_request)
        current_app.logger.info("Started listening for return requests...")
        channel.start_consuming()
    except Exception as e:
        current_app.logger.error(f"Error in return request consumer: {str(e)}")
