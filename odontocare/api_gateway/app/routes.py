import requests
from flask import Blueprint, jsonify, request, current_app, Response


gateway_bp = Blueprint("gateway_bp", __name__)


@gateway_bp.route("/health", methods=["GET"])
def health():
    # Endpoint técnico para comprobar que el API Gateway está activo
    return jsonify({
        "blueprint": "gateway_bp",
        "service": "api_gateway",
        "status": "ok"
    }), 200


def forward_request(service_url, path):
    # Construimos la URL final del microservicio destino
    target_url = f"{service_url}/{path}"

    # Copiamos las cabeceras originales, incluyendo Authorization
    headers = {
        key: value
        for key, value in request.headers
        if key.lower() != "host"
    }

    try:
        # Reenviamos la petición al microservicio correspondiente
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            json=request.get_json(silent=True),
            params=request.args,
            timeout=10
        )

    except requests.RequestException:
        return jsonify({
            "error": "No se pudo conectar con el microservicio destino"
        }), 502

    # Devolvemos al cliente la respuesta original del microservicio
    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type", "application/json")
    )


@gateway_bp.route("/api/auth/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_auth(path):
    return forward_request(
        current_app.config["USUARIOS_SERVICE_URL"],
        f"auth/{path}"
    )


@gateway_bp.route("/api/admin/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_admin(path):
    # Reenvía peticiones administrativas al microservicio administracion
    return forward_request(
        current_app.config["ADMIN_SERVICE_URL"],
        f"admin/{path}"
    )


@gateway_bp.route("/api/citas", methods=["GET", "POST"])
def proxy_citas_root():
    # Reenvía peticiones a la raíz del módulo de citas
    return forward_request(
        current_app.config["CITAS_SERVICE_URL"],
        "citas"
    )


@gateway_bp.route("/api/citas/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_citas(path):
    # Reenvía peticiones de citas al microservicio citas
    return forward_request(
        current_app.config["CITAS_SERVICE_URL"],
        f"citas/{path}"
    )