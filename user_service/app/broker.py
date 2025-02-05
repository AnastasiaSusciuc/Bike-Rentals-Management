import pika
import json
from flask import current_app
from .cache import rental_response_cache, return_response_cache
from kafka import KafkaConsumer
from flask_mail import Mail, Message

import logging

logging.getLogger("pika").setLevel(logging.INFO)
# logging.getLogger("kafka").setLevel(logging.ERROR)


#####################################
# KAFKA CONSUMER FOR bike BORROWING
#####################################


def send_email_notification(user_id, bike_id, mail):
    """Send an email notification to the user about bike availability."""
    try:
        user_email = 'susciuc.anastasia@gmail.com'  # get the email of the user
        username = "Anastasia"

        subject = f"Bike Availability Update For Bike {bike_id}"
        body = f"Dear {username},\n\nThe bike you were waiting for is now available!! Yaaay! Don't miss the chance to " \
               f"rent it!\n\nThank you! "

        msg = Message(subject, recipients=[user_email], body=body, sender="noreply@library.com")

        mail.send(msg)
        current_app.logger.info(f"***** Email sent to {user_email} about bike {bike_id} availability.")

    except Exception as e:
        current_app.logger.error(f"Failed to send email notification: {str(e)}")


def start_kafka_notification_consumer(mail):
    """Starts a Kafka consumer to listen for notifications about bike availability."""
    with current_app.app_context():
        try:

            # consumer = KafkaConsumer(
            #     'borrow-requests',
            #     bootstrap_servers='kafka1:9092',
            #     group_id='user-service-group',
            #     value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            #     auto_offset_reset='earliest'
            # )
            consumer = KafkaConsumer(
                'bike-availability',
                bootstrap_servers='kafka1:9092',
                group_id='user-service-group',
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest'
                        )

            current_app.logger.info("Kafka consumer for bike availability notifications started.")

            for message in consumer:
                event = message.value
                user_id = event.get('user_id')
                bike_id = event.get('bike_id')
                timestamp = event.get('timestamp')

                current_app.logger.info(
                    f"Received Kafka notification event: User {user_id} is waiting for bike {bike_id} (at {timestamp})."
                )

                send_email_notification(user_id, bike_id, mail)

                current_app.logger.info(
                    f"Notification sent to User {user_id} about bike {bike_id} availability."
                )

        except Exception as e:
            current_app.logger.error(f"Error in Kafka notification consumer: {str(e)}")


###########################
# rent bike
###########################

def start_rent_response_consumer():
    with current_app.app_context():
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()

            # Declare the response queue
            channel.queue_declare(queue='rent_response_queue', durable=True)

            # Define the callback function
            def on_rent_response(ch, method, properties, body):
                response = json.loads(body)
                user_id = response['user_id']
                bike_id = response['bike_id']
                status = response['status']
                message = response['message']

                # Log or process the response
                current_app.logger.info(f"rent response received for user {user_id}: {status} - {message}")
                # Put the response in the shared queue
                rental_response_cache.put(response)
                # Acknowledge the message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            # Start consuming
            channel.basic_consume(queue='rent_response_queue', on_message_callback=on_rent_response)
            current_app.logger.info("Listening for rent responses...")
            channel.start_consuming()
        except Exception as e:
            current_app.logger.error(f"Error in rent response consumer: {str(e)}")
            return {'status': 'failure', 'message': 'Error processing your rent request.'}


def send_rental_request(user_id, bike_id):
    message = {
        'user_id': user_id,
        'bike_id': bike_id,
    }

    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the queue (ensure the queue exists before publishing)
        channel.queue_declare(queue='rent_request_queue', durable=True)

        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key='rent_request_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Persist the message
            )
        )

        current_app.logger.info(f"Sent rent request for user {user_id} and bike {bike_id}")

        connection.close()

    except Exception as e:
        current_app.logger.error(f"Error sending rent request: {str(e)}")
        raise e


###########################
# RETURN bike
###########################

def send_return_request(user_id, bike_id):
    """Send a return request message to the bike Service via RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the return request queue
        channel.queue_declare(queue='return_request_queue', durable=True)

        request_message = json.dumps({
            "user_id": user_id,
            "bike_id": bike_id
        })

        # Send the request to the return_request_queue
        channel.basic_publish(
            exchange='',
            routing_key='return_request_queue',
            body=request_message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )

        current_app.logger.info(f"Sent return request for user {user_id} and bike {bike_id}")
        connection.close()

    except Exception as e:
        current_app.logger.error(f"Error sending return request: {e}")


def start_return_response_consumer():
    """Listen for the return response from bike Service."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the response queue (if not already declared)
        channel.queue_declare(queue='return_response_queue', durable=True)

        def on_return_response(ch, method, properties, body):
            """Handle the return response message."""
            response = json.loads(body)
            user_id = response['user_id']
            bike_id = response['bike_id']
            status = response['status']
            message = response['message']

            # Log the response or use it to update the front-end
            current_app.logger.info(f"Return response received for user {user_id}: {status} - {message}")
            return_response_cache.put(response)
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Start consuming
        channel.basic_consume(queue='return_response_queue', on_message_callback=on_return_response)
        current_app.logger.info("Listening for return responses...")
        channel.start_consuming()
    except Exception as e:
        current_app.logger.error(f"Error in return response consumer: {str(e)}")
