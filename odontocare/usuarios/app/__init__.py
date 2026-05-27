from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, jwt
from app.blueprints.auth.routes import auth_bp


def create_app():
    # Creamos la aplicación Flask
    app = Flask(__name__)

    # Permitimos que los caracteres Unicode se muestren sin escapar
    app.json.ensure_ascii = False

    # Cargamos la configuración del microservicio
    app.config.from_object(Config)

    # Inicializamos las extensiones con esta app Flask
    db.init_app(app)
    jwt.init_app(app)

    # Registramos el blueprint de autenticación
    app.register_blueprint(auth_bp)

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