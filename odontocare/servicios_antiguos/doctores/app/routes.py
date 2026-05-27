from flask import Blueprint, jsonify

doctores_bp = Blueprint("doctores", __name__)

@doctores_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "doctores",
        "status": "ok"
    }), 200