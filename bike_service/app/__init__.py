from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from .broker import start_rent_request_consumer, start_return_request_consumer
from .models import db
import os
import threading

project_root = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(project_root, '..', '.env')
load_dotenv(env_file_path)

jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.logger.info("Bike Service started.")

    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.logger.info(os.getenv('DATABASE_URI'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB limit

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from .routes import bike_bp
    app.register_blueprint(bike_bp, url_prefix='/bike')

    # Background thread for RabbitMQ consumer
    def start_consumer_rent_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_rent_request_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ bike service rental consumer thread started.")

    def start_consumer_return_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_return_request_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ bike service return consumer thread started.")

    def start_consumer_threads():
        start_consumer_rent_thread()
        start_consumer_return_thread()

    # Start the consumer thread when the app starts
    start_consumer_threads()

    return app
