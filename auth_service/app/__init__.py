from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from .models import db
import os

# Load environment variables
# # dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# load_dotenv("/Users/anastasiasusciuc/Desktop/Ani-SOA-App/auth_service/.env")

project_root = os.path.dirname(os.path.abspath(__file__))
# Resolve the correct path to the .env file in the project root directory
env_file_path = os.path.join(project_root, '..', '.env')

# Load the .env file
load_dotenv(env_file_path)

print("PATHH: ", env_file_path)
# Initialize extensions
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/auth/*": {
            "origins": ["http://localhost:4201"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

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
    from .routes import auth_routes
    app.register_blueprint(auth_routes, url_prefix='/auth')

    return app