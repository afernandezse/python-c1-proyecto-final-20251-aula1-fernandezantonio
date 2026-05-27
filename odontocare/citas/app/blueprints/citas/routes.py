import jwt
from functools import wraps
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from app.models import Cita
from app.extensions import db
import requests



citas_bp = Blueprint("citas_bp", __name__)


def roles_required(*roles_permitidos):
    # Decorador para restringir endpoints según el rol incluido en el JWT
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({
                    "error": "Token no proporcionado o formato incorrecto"
                }), 401

            token = auth_header.split(" ")[1]

            try:
                payload = jwt.decode(
                    token,
                    current_app.config["JWT_SECRET_KEY"],
                    algorithms=["HS256"]
                )

                role = payload.get("role")

                if role not in roles_permitidos:
                    return jsonify({
                        "error": "No tiene permisos para realizar esta acción",
                        "roles_permitidos": list(roles_permitidos),
                        "rol_actual": role
                    }), 403

                return func(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expirado"}), 401

            except jwt.InvalidTokenError:
                return jsonify({"error": "Token inválido"}), 401

        return wrapper
    return decorator


def validar_entidad_administracion(endpoint, token):
    # Consulta al microservicio de administración para validar que una entidad existe.
    # No accedemos directamente a administracion.db, sino por REST.
    url = f"{current_app.config['ADMIN_SERVICE_URL']}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

    except requests.RequestException:
        return False, {
            "error": "No se pudo conectar con el microservicio de administración"
        }

    if response.status_code == 200:
        return True, response.json()

    return False, response.json()


ESTADOS_CITA = ["PROGRAMADA", "COMPLETADA", "CANCELADA"]


@citas_bp.route("/health", methods=["GET"])
def health():
    # Endpoint técnico para comprobar que el microservicio está activo
    return jsonify({
        "service": "citas",
        "blueprint": "citas_bp",
        "status": "ok"
    }), 200


@citas_bp.route("/citas", methods=["POST"])
@roles_required("admin", "secretaria")
def create_cita():
    # Recibimos los datos de la cita en formato JSON
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    id_paciente = data.get("id_paciente")
    id_doctor = data.get("id_doctor")
    id_clinica = data.get("id_clinica")
    fecha_hora_texto = data.get("fecha_hora")
    motivo = data.get("motivo")
    estado = data.get("estado", "PROGRAMADA")

    # Validamos campos obligatorios
    if not id_paciente or not id_doctor or not id_clinica or not fecha_hora_texto:
        return jsonify({
            "error": "Los campos id_paciente, id_doctor, id_clinica y fecha_hora son obligatorios"
        }), 400

    # Validamos el estado de la cita
    if estado not in ESTADOS_CITA:
        return jsonify({
            "error": "Estado de cita no válido",
            "estados_validos": ESTADOS_CITA
        }), 400
    
    # Recuperamos el token recibido para reutilizarlo en la llamada REST a administración
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]

    # Validamos que el paciente exista en el microservicio de administración
    paciente_ok, paciente_response = validar_entidad_administracion(
        f"/admin/pacientes/{id_paciente}",
        token
    )

    if not paciente_ok:
        return jsonify({
            "error": "Paciente no válido o no encontrado",
            "detalle": paciente_response
        }), 400

    # Validamos que el doctor exista en el microservicio de administración
    doctor_ok, doctor_response = validar_entidad_administracion(
        f"/admin/doctores/{id_doctor}",
        token
    )

    if not doctor_ok:
        return jsonify({
            "error": "Doctor no válido o no encontrado",
            "detalle": doctor_response
        }), 400

    # Validamos que la clínica exista en el microservicio de administración
    clinica_ok, clinica_response = validar_entidad_administracion(
        f"/admin/clinicas/{id_clinica}",
        token
    )

    if not clinica_ok:
        return jsonify({
            "error": "Clínica no válida o no encontrada",
            "detalle": clinica_response
        }), 400

    try:
        # Convertimos la fecha recibida como texto a objeto datetime
        # Formato esperado: YYYY-MM-DD HH:MM
        fecha_hora = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M")

    except ValueError:
        return jsonify({
            "error": "Formato de fecha_hora inválido. Use YYYY-MM-DD HH:MM"
        }), 400

    # Validamos que el doctor no tenga ya una cita programada en la misma fecha y hora
    cita_existente = Cita.query.filter_by(
        id_doctor=id_doctor,
        fecha_hora=fecha_hora,
        estado="PROGRAMADA"
    ).first()

    if cita_existente:
        return jsonify({
            "error": "El doctor ya tiene una cita programada en esa fecha y hora"
        }), 409
    
    # Validamos que la clínica no tenga ya una cita programada en la misma fecha y hora
    conflicto_clinica = Cita.query.filter_by(
        id_clinica=id_clinica,
        fecha_hora=fecha_hora,
        estado="PROGRAMADA"
    ).first()

    if conflicto_clinica:
        return jsonify({
            "error": "La clínica ya tiene una cita programada en esa fecha y hora"
        }), 409

    # Creamos la cita
    cita = Cita(
        id_paciente=id_paciente,
        id_doctor=id_doctor,
        id_clinica=id_clinica,
        fecha_hora=fecha_hora,
        motivo=motivo,
        estado=estado
    )

    # Guardamos la cita en la base de datos
    db.session.add(cita)
    db.session.commit()

    return jsonify({
        "message": "Cita creada correctamente",
        "cita": cita.to_dict()
    }), 201


@citas_bp.route("/citas", methods=["GET"])
@roles_required("admin", "secretaria", "medico", "paciente")
def get_citas():
    # Obtenemos el token de la cabecera Authorization
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]

    try:
        # Decodificamos el token para conocer el rol del usuario
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401

    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

    role = payload.get("role")
    user_id = int(payload.get("sub"))

    # Consulta base sobre la tabla de citas
    query = Cita.query

    if role == "admin":
        # El administrador puede filtrar por doctor, clínica, paciente, fecha o estado
        id_doctor = request.args.get("id_doctor")
        id_clinica = request.args.get("id_clinica")
        id_paciente = request.args.get("id_paciente")
        estado = request.args.get("estado")
        fecha = request.args.get("fecha")

        if id_doctor:
            query = query.filter(Cita.id_doctor == int(id_doctor))

        if id_clinica:
            query = query.filter(Cita.id_clinica == int(id_clinica))

        if id_paciente:
            query = query.filter(Cita.id_paciente == int(id_paciente))

        if estado:
            query = query.filter(Cita.estado == estado)

        if fecha:
            try:
                fecha_inicio = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "error": "Formato de fecha inválido. Use YYYY-MM-DD"
                }), 400

            fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59)

            query = query.filter(
                Cita.fecha_hora >= fecha_inicio,
                Cita.fecha_hora <= fecha_fin
            )

    elif role == "secretaria":
        # La secretaria puede consultar citas y opcionalmente filtrar por fecha
        fecha = request.args.get("fecha")

        if fecha:
            try:
                fecha_inicio = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "error": "Formato de fecha inválido. Use YYYY-MM-DD"
                }), 400

            fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59)

            query = query.filter(
                Cita.fecha_hora >= fecha_inicio,
                Cita.fecha_hora <= fecha_fin
            )

    elif role == "medico":
        # El médico solo puede consultar sus propias citas
        # En esta versión asumimos que id_doctor coincide con el id de usuario del médico
        query = query.filter(Cita.id_doctor == user_id)

    elif role == "paciente":
        # El paciente solo puede consultar sus propias citas
        # En esta versión asumimos que id_paciente coincide con el id de usuario del paciente
        query = query.filter(Cita.id_paciente == user_id)

    # Obtener listado de citas con paginación
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    citas = pagination.items

    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "citas": [cita.to_dict() for cita in citas]
    }), 200


@citas_bp.route("/citas/<int:id>", methods=["GET"])
@roles_required("admin", "secretaria", "medico")
def get_cita(id):
    # Buscamos una cita por su identificador
    cita = Cita.query.get(id)

    if not cita:
        return jsonify({
            "error": "Cita no encontrada"
        }), 404

    return jsonify({
        "cita": cita.to_dict()
    }), 200


@citas_bp.route("/citas/<int:id>", methods=["PUT"])
@roles_required("admin", "secretaria")
def update_cita(id):
    # Buscamos la cita que se quiere actualizar
    cita = Cita.query.get(id)

    if not cita:
        return jsonify({
            "error": "Cita no encontrada"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    # Actualizamos solo los campos recibidos
    cita.id_paciente = data.get("id_paciente", cita.id_paciente)
    cita.id_doctor = data.get("id_doctor", cita.id_doctor)
    cita.id_clinica = data.get("id_clinica", cita.id_clinica)
    cita.motivo = data.get("motivo", cita.motivo)

    estado = data.get("estado", cita.estado)

    if estado not in ESTADOS_CITA:
        return jsonify({
            "error": "Estado de cita no válido",
            "estados_validos": ESTADOS_CITA
        }), 400

    cita.estado = estado

    # Si se recibe una nueva fecha, la convertimos y validamos
    if "fecha_hora" in data:
        try:
            nueva_fecha_hora = datetime.strptime(
                data.get("fecha_hora"),
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return jsonify({
                "error": "Formato de fecha_hora inválido. Use YYYY-MM-DD HH:MM"
            }), 400

        cita.fecha_hora = nueva_fecha_hora

    # Validamos que no exista otra cita programada para el mismo doctor en esa fecha y hora
    conflicto = Cita.query.filter(
        Cita.id != cita.id,
        Cita.id_doctor == cita.id_doctor,
        Cita.fecha_hora == cita.fecha_hora,
        Cita.estado == "PROGRAMADA"
    ).first()

    if conflicto and cita.estado == "PROGRAMADA":
        return jsonify({
            "error": "El doctor ya tiene otra cita programada en esa fecha y hora"
        }), 409

    db.session.commit()

    return jsonify({
        "message": "Cita actualizada correctamente",
        "cita": cita.to_dict()
    }), 200


@citas_bp.route("/citas/<int:id>", methods=["DELETE"])
@roles_required("admin", "secretaria")
def delete_cita(id):
    # Buscamos la cita que se quiere eliminar
    cita = Cita.query.get(id)

    if not cita:
        return jsonify({
            "error": "Cita no encontrada"
        }), 404

    db.session.delete(cita)
    db.session.commit()

    return jsonify({
        "message": "Cita eliminada correctamente"
    }), 200