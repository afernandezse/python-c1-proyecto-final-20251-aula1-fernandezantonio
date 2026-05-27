from flask import Flask
from app.routes import pacientes_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(pacientes_bp)
    return app