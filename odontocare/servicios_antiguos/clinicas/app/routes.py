from flask import Blueprint, jsonify

clinicas_bp = Blueprint("clinicas", __name__)

@clinicas_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "clinicas",
        "status": "ok"
    }), 200