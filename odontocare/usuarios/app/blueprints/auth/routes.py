from flask import Blueprint, jsonify, request, current_app
from app.extensions import db
from app.models import User, ROLES_VALIDOS
from datetime import datetime, timedelta, timezone
import jwt
from app.models import User


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "usuarios",
        "blueprint": "auth_bp",
        "status": "ok"
    }), 200


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Si no se indica rol, por defecto se asigna "paciente"
    role = data.get("role", "paciente")

    # Validamos que el rol recibido esté permitido
    if role not in ROLES_VALIDOS:
        return jsonify({
            "error": "Rol no válido",
            "roles_validos": list(ROLES_VALIDOS)
        }), 400
    
    # Verificamos si el username ya existe
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({
            "error": "El nombre de usuario ya existe"
        }), 409

    # Verificamos si el email ya existe
    existing_email = User.query.filter_by(email=email).first()

    if existing_email:
        return jsonify({
            "error": "El email ya está registrado"
        }), 409

    # Creamos el usuario
    user = User(
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Usuario registrado correctamente",
        "user": user.to_dict()
    }), 201
    

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    # Recibimos las credenciales en formato JSON
    credenciales = request.get_json()

    email = credenciales.get("email")
    password = credenciales.get("password")

    # Validamos campos obligatorios
    if not email or not password:
        return jsonify({
            "error": "Email y contraseña son obligatorios"
        }), 400

    # Buscamos el usuario en SQLite mediante SQLAlchemy
    user = User.query.filter_by(email=email).first()

    # Validamos que exista y que la contraseña coincida con el hash guardado
    if not user or not user.check_password(password):
        return jsonify({
            "error": "Credenciales inválidas"
        }), 401

    # Creamos el payload del token JWT
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    # Firmamos el token con la clave secreta de la aplicación
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({
        "message": "Inicio de sesión correcto",
        "token": token,
        "user": user.to_dict()
    }), 200

@auth_bp.route("/auth/profile", methods=["GET"])
def profile():
    # Obtenemos la cabecera Authorization
    auth_header = request.headers.get("Authorization")

    # Validamos que exista la cabecera y que use el formato Bearer
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "Token no proporcionado o formato incorrecto"
        }), 401

    # Extraemos el token quitando el prefijo "Bearer "
    token = auth_header.split(" ")[1]

    try:
        # Decodificamos el token usando la misma clave secreta
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )

        # Recuperamos el id del usuario desde el payload
        user_id = payload.get("sub")

        # Buscamos el usuario en la base de datos
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                "error": "Usuario no encontrado"
            }), 404

        return jsonify({
            "message": "Perfil obtenido correctamente",
            "user": user.to_dict()
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({
            "error": "Token expirado"
        }), 401

    except jwt.InvalidTokenError:
        return jsonify({
            "error": "Token inválido"
        }), 401