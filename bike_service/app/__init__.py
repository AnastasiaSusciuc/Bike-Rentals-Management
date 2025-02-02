from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from .models import db
import os

load_dotenv("/Users/anastasiasusciuc/Desktop/Ani-SOA-App/bike_service/.env")
print(os.path.abspath('instance/auth.db'))


jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Use SQLite instead of PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from .routes import bike_bp
    app.register_blueprint(bike_bp)

    return app
