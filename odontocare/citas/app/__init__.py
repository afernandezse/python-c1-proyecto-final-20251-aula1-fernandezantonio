from flask import Flask, jsonify
from app.config import Config
from app.extensions import db
from app.blueprints.citas.routes import citas_bp


def create_app():
    # Creamos la aplicación Flask
    app = Flask(__name__)

    # Permitimos que los caracteres Unicode se muestren sin escapar
    app.json.ensure_ascii = False

    # Cargamos la configuración del microservicio
    app.config.from_object(Config)

    # Inicializamos SQLAlchemy con esta aplicación
    db.init_app(app)

    # Registramos el blueprint de citas
    app.register_blueprint(citas_bp)

    # Creamos las tablas si no existen
    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app