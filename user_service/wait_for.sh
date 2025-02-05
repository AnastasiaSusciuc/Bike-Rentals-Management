#!/bin/bash

# Wait for RabbitMQ to be healthy
echo "Waiting for RabbitMQ to become healthy..."
until curl -s -u guest:guest http://rabbitmq:15672/api/overview > /dev/null; do
    echo "RabbitMQ is not healthy yet, retrying in 5 seconds..."
    sleep 5
done

# Once RabbitMQ is healthy, start the Flask application
echo "RabbitMQ is healthy, starting Bike Service..."
exec flask run  # Or the command to start your Flask app
