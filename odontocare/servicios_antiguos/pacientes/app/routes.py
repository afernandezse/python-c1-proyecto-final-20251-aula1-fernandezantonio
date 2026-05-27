from flask import Blueprint, jsonify

pacientes_bp = Blueprint("pacientes", __name__)

@pacientes_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "pacientes",
        "status": "ok"
    }), 200