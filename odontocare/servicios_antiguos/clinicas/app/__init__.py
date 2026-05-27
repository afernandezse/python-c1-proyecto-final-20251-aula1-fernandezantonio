from flask import Flask
from app.routes import clinicas_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(clinicas_bp)
    return app