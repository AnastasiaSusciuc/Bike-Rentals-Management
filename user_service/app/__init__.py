from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    from .routes import auth_routes
    app.register_blueprint(auth_routes)

    return app