from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from .models import db
import os

project_root = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(project_root, '..', '.env')

load_dotenv(env_file_path)

# Initialize extensions
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    CORS(app)
    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
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