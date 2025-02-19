# Bike Rentals App

Bike Rental Management Application for Service-Oriented Architecture class

## Introduction

This project is a microservice-based application designed to manage authentication, user, and bike-related functionalities. It is fully containerized using Docker, with all components orchestrated and managed through Docker Compose.

The system integrates several backend services developed in Python with Flask, a microfrontend architecture built with Angular and Module Federation (for more details, refer to this [repository](https://github.com/AnastasiaSusciuc/MFE-BikeManagementApp)), and an NGINX load-balanced API gateway for efficient request routing. Additionally, the application supports serverless functions via AWS Lambda. Communication between microservices is handled through RabbitMQ, while event streaming is managed with Apache Kafka. The REST API is secured using JWT tokens to ensure safe authentication and authorization.

Here is an overview of the main components of the application:

### Backend Services
Auth Service: Handles user authentication and token generation.
User Service: Manages user-related data and operations, such as fetching user profiles.
Bike Service: Provides bike management features, with redundancy via a backup instance.

### API Gateway
The API Gateway, built with NGINX, serves as a reverse proxy and load balancer (for the bike microservice), routing requests to the appropriate backend services and the AWS Lambda-based serverless function.

### Database Layer
Each microservice is paired with its own dedicated SQLite instance to ensure data isolation and integrity.

### Message Brokers and Event Streaming
Message Brokering: Implemented with RabbitMQ, enabling asynchronous communication between the User Service and the Bike Service to manage bike rentals and returns. When a user rents or returns a bike, the User Service sends a message to the Bike Service via RabbitMQ to update bike availability.
Event Streaming: Utilizes Apache Kafka for real-time data streaming and processing. Kafka facilitates event-driven communication between the Bike Service and t

### FaaS (Function as a Service)

A Lambda function, /get-garages, demonstrates serverless computing in this application. Built using AWS Lambda, this function retrieves the number of garages needed for storing all the bikes. By using serverless architecture, it allows the system to handle user-specific data queries without the need for a dedicated backend service. The function is deployed and managed using the Serverless Framework, ensuring efficient deployment to AWS.

The following architecture diagram illustrates how all components come together: 

