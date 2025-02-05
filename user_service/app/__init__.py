import logging

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from .broker import start_rent_response_consumer, start_return_response_consumer, start_kafka_notification_consumer
from .models import db
from flask_mail import Mail
import os
import threading

# Load environment variables

project_root = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(project_root, '..', '.env')
load_dotenv(env_file_path)

# Initialize extensions
jwt = JWTManager()
migrate = Migrate()
mail = Mail()


def create_app():
    app = Flask(__name__)
    # app.config.from_object(Config)

    # Load email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    # app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'maria.andreea.farcas@gmail.com')
    # app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'qinciB-surpiv-suscy7')

    app.config['MAIL_USERNAME'] = 'maria.andreea.farcas@gmail.com'  # todo
    app.config['MAIL_PASSWORD'] = 'hsoi bixs ameu vpfn'
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@yourdomain.com'

    app.config['DEBUG'] = True  # todo remove
    logging.basicConfig(level=logging.INFO)

    CORS(app)
    mail.init_app(app)

    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    def start_rent_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_rent_response_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ user service rent consumer thread started.")

    def start_return_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_return_response_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ user service return consumer thread started.")

    def start_kafka_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_kafka_notification_consumer(mail)

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("Kafka borrow consumer thread started.")

    # Start the consumer threads when the app starts
    start_rent_consumer_thread()
    start_return_consumer_thread()
    start_kafka_consumer_thread()

    return app
