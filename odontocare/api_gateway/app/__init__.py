from flask import Flask, jsonify
from app.config import Config
from app.routes import gateway_bp


def create_app():
    # Creamos la aplicación Flask
    app = Flask(__name__)

    # Permitimos que los caracteres Unicode se muestren sin escapar
    app.json.ensure_ascii = False

    # Cargamos la configuración del API Gateway
    app.config.from_object(Config)

    # Registramos las rutas del gateway
    app.register_blueprint(gateway_bp)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app