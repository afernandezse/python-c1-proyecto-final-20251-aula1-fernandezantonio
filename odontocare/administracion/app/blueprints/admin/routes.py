from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Patient, Doctor, Clinica
from functools import wraps
import jwt
from flask import Blueprint, jsonify, request, current_app


admin_bp = Blueprint("admin_bp", __name__)

def roles_required(*roles_permitidos):
    # Decorador genérico para restringir endpoints según el rol incluido en el JWT
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Leemos la cabecera Authorization
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({
                    "error": "Token no proporcionado o formato incorrecto"
                }), 401

            # Extraemos el token eliminando el prefijo Bearer
            token = auth_header.split(" ")[1]

            try:
                # Decodificamos el token con la misma clave usada en usuarios
                payload = jwt.decode(
                    token,
                    current_app.config["JWT_SECRET_KEY"],
                    algorithms=["HS256"]
                )

                role = payload.get("role")

                # Validamos que el rol esté autorizado
                if role not in roles_permitidos:
                    return jsonify({
                        "error": "No tiene permisos para realizar esta acción",
                        "roles_permitidos": list(roles_permitidos),
                        "rol_actual": role
                    }), 403

                return func(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({
                    "error": "Token expirado"
                }), 401

            except jwt.InvalidTokenError:
                return jsonify({
                    "error": "Token inválido"
                }), 401

        return wrapper
    return decorator


@admin_bp.route("/health", methods=["GET"])
def health():
    # Endpoint técnico para comprobar que el servicio está activo
    return jsonify({
        "service": "administracion",
        "blueprint": "admin_bp",
        "status": "ok"
    }), 200


## CRUD pacientes
@admin_bp.route("/admin/pacientes", methods=["POST"])
@roles_required("admin", "secretaria")
def create_patient():
    # Recibimos los datos del paciente en formato JSON
    data = request.get_json()

    # Validamos que el cuerpo de la petición no esté vacío
    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    nombre = data.get("nombre")
    telefono = data.get("telefono")
    id_usuario = data.get("id_usuario")
    estado = data.get("estado", "ACTIVO")

    # Validamos campos obligatorios
    if not nombre :
        return jsonify({
            "error": "Los campos nombre es obligatorio"
        }), 400

    # Validamos el estado del paciente
    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    # Creamos el objeto Patient
    patient = Patient(
        nombre=nombre,
        telefono=telefono,
        id_usuario=id_usuario,
        estado=estado
    )

    # Guardamos el paciente en la base de datos
    db.session.add(patient)
    db.session.commit()

    return jsonify({
        "message": "Paciente creado correctamente",
        "patient": patient.to_dict()
    }), 201

@admin_bp.route("/admin/pacientes", methods=["GET"])
@roles_required("admin", "secretaria", "medico")
def get_patients():
    # Obtenemos los parámetros de paginación desde la URL
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Aplicamos paginación a la consulta de pacientes
    pagination = Patient.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    patients = pagination.items

    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "patients": [patient.to_dict() for patient in patients]
    }), 200


@admin_bp.route("/admin/pacientes/<int:id_paciente>", methods=["GET"])
@roles_required("admin", "secretaria", "medico")
def get_patient(id_paciente):
    # Buscamos un paciente por su identificador
    patient = Patient.query.get(id_paciente)

    if not patient:
        return jsonify({
            "error": "Paciente no encontrado"
        }), 404

    return jsonify({
        "patient": patient.to_dict()
    }), 200


@admin_bp.route("/admin/pacientes/<int:id_paciente>", methods=["PUT"])
@roles_required("admin", "secretaria")
def update_patient(id_paciente):
    # Buscamos el paciente que se quiere actualizar
    patient = Patient.query.get(id_paciente)

    if not patient:
        return jsonify({
            "error": "Paciente no encontrado"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    # Actualizamos solo los campos recibidos
    patient.nombre = data.get("nombre", patient.nombre)
    patient.telefono = data.get("telefono", patient.telefono)
    patient.id_usuario = data.get("id_usuario", patient.id_usuario)

    estado = data.get("estado", patient.estado)

    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    patient.estado = estado

    db.session.commit()

    return jsonify({
        "message": "Paciente actualizado correctamente",
        "patient": patient.to_dict()
    }), 200


@admin_bp.route("/admin/pacientes/<int:id_paciente>", methods=["DELETE"])
@roles_required("admin", "secretaria")
def delete_patient(id_paciente):
    # Buscamos el paciente que se quiere eliminar
    patient = Patient.query.get(id_paciente)

    if not patient:
        return jsonify({
            "error": "Paciente no encontrado"
        }), 404

    db.session.delete(patient)
    db.session.commit()

    return jsonify({
        "message": "Paciente eliminado correctamente"
    }), 200


## CRUD médicos
@admin_bp.route("/admin/doctores", methods=["POST"])
@roles_required("admin", "secretaria")
def create_doctor():
    # Recibimos los datos del doctor en formato JSON
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    nombre = data.get("nombre")
    especialidad = data.get("especialidad")
    id_usuario = data.get("id_usuario")
    estado = data.get("estado", "ACTIVO")

    # Validamos campos obligatorios
    if not nombre or not especialidad:
        return jsonify({
            "error": "Los campos nombre y especialidad son obligatorios"
        }), 400

    # Validamos el estado del doctor
    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    # Creamos el objeto Doctor
    doctor = Doctor(
        nombre=nombre,
        especialidad=especialidad,
        id_usuario=id_usuario,
        estado=estado
    )

    # Guardamos el doctor en la base de datos
    db.session.add(doctor)
    db.session.commit()

    return jsonify({
        "message": "Doctor creado correctamente",
        "doctor": doctor.to_dict()
    }), 201


@admin_bp.route("/admin/doctores", methods=["GET"])
@roles_required("admin", "secretaria")
def get_doctors():
    # Consultamos los doctores con paginación
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = Doctor.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    doctors = pagination.items

    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "doctors": [doctor.to_dict() for doctor in doctors]
    }), 200


@admin_bp.route("/admin/doctores/<int:id>", methods=["GET"])
@roles_required("admin", "secretaria")
def get_doctor(id):
    # Buscamos un doctor por su identificador
    doctor = Doctor.query.get(id)

    if not doctor:
        return jsonify({
            "error": "Doctor no encontrado"
        }), 404

    return jsonify({
        "doctor": doctor.to_dict()
    }), 200


@admin_bp.route("/admin/doctores/<int:id_doctor>", methods=["PUT"])
@roles_required("admin", "secretaria")
def update_doctor(id_doctor):
    # Buscamos el doctor que se quiere actualizar
    doctor = Doctor.query.get(id_doctor)

    if not doctor:
        return jsonify({
            "error": "Doctor no encontrado"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    # Actualizamos solo los campos recibidos
    doctor.nombre = data.get("nombre", doctor.nombre)
    doctor.especialidad = data.get("especialidad", doctor.especialidad)
    doctor.id_usuario = data.get("id_usuario", doctor.id_usuario)

    estado = data.get("estado", doctor.estado)

    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    doctor.estado = estado

    db.session.commit()

    return jsonify({
        "message": "Doctor actualizado correctamente",
        "doctor": doctor.to_dict()
    }), 200


@admin_bp.route("/admin/doctores/<int:id_doctor>", methods=["DELETE"])
@roles_required("admin", "secretaria")
def delete_doctor(id_doctor):
    # Buscamos el doctor que se quiere eliminar
    doctor = Doctor.query.get(id_doctor)

    if not doctor:
        return jsonify({
            "error": "Doctor no encontrado"
        }), 404

    db.session.delete(doctor)
    db.session.commit()

    return jsonify({
        "message": "Doctor eliminado correctamente"
    }), 200

## CRUD clínicas

@admin_bp.route("/admin/clinicas", methods=["POST"])
@roles_required("admin", "secretaria")
def create_clinic():
    # Recibimos los datos de la clínica en formato JSON
    data = request.get_json()


    # Validamos que el cuerpo de la petición no esté vacío
    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    nombre = data.get("nombre")
    direccion = data.get("direccion")
    estado = data.get("estado", "ACTIVO")

    # Validamos campos obligatorios
    if not nombre:
        return jsonify({
            "error": "El campo nombre es obligatorio"
        }), 400

    if not direccion:
        return jsonify({
            "error": "El campo direccion es obligatorio"
        }), 400

    # Validamos el estado de la clínica
    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    # Creamos el objeto Clinica
    clinic = Clinica(

        nombre=nombre,
        direccion=direccion,
        estado=estado
    )

    # Guardamos la clínica en la base de datos
    db.session.add(clinic)
    db.session.commit()

    return jsonify({
        "message": "Clínica creada correctamente",
        "clinic": clinic.to_dict()
    }), 201


@admin_bp.route("/admin/clinicas", methods=["GET"])
@roles_required("admin", "secretaria", "medico")
def get_clinics():
    # Consultamos las clínicas con paginación
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = Clinica.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    clinics = pagination.items

    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "clinics": [clinic.to_dict() for clinic in clinics]
    }), 200


@admin_bp.route("/admin/clinicas/<int:id>", methods=["GET"])
@roles_required("admin", "secretaria", "medico")
def get_clinic(id):
    # Buscamos una clínica por su identificador
    clinic = Clinica.query.get(id)

    if not clinic:
        return jsonify({
            "error": "Clínica no encontrada"
        }), 404

    return jsonify({
        "clinic": clinic.to_dict()
    }), 200


@admin_bp.route("/admin/clinicas/<int:id>", methods=["PUT"])
@roles_required("admin", "secretaria")
def update_clinic(id):
    # Buscamos la clínica a actualizar
    clinic = Clinica.query.get(id)

    if not clinic:
        return jsonify({
            "error": "Clínica no encontrada"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibieron datos en formato JSON"
        }), 400

    # Actualizamos solo los campos recibidos
    clinic.nombre = data.get("nombre", clinic.nombre)
    clinic.direccion = data.get("direccion", clinic.direccion)

    estado = data.get("estado", clinic.estado)

    if estado not in ["ACTIVO", "INACTIVO"]:
        return jsonify({
            "error": "Estado no válido",
            "estados_validos": ["ACTIVO", "INACTIVO"]
        }), 400

    clinic.estado = estado

    db.session.commit()

    return jsonify({
        "message": "Clínica actualizada correctamente",
        "clinic": clinic.to_dict()
    }), 200


@admin_bp.route("/admin/clinicas/<int:id>", methods=["DELETE"])
@roles_required("admin", "secretaria")
def delete_clinic(id):
    # Buscamos la clínica que se quiere eliminar
    clinic = Clinica.query.get(id)

    if not clinic:
        return jsonify({
            "error": "Clínica no encontrada"
        }), 404

    db.session.delete(clinic)
    db.session.commit()

    return jsonify({
        "message": "Clínica eliminada correctamente"
    }), 200

@admin_bp.route("/admin/pacientes/bulk", methods=["POST"])
@roles_required("admin", "secretaria")
def create_patients_bulk():
    # Recibimos una lista de pacientes en formato JSON
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({
            "error": "Se esperaba una lista JSON de pacientes"
        }), 400

    pacientes_creados = []
    errores = []

    for index, item in enumerate(data):
        # Extraemos los campos de cada paciente
        nombre = item.get("nombre")
        telefono = item.get("telefono")
        id_usuario = item.get("id_usuario")
        estado = item.get("estado", "ACTIVO")

        # Validamos campos obligatorios
        if not nombre or not telefono:
            errores.append({
                "index": index,
                "error": "Los campos nombre y telefono son obligatorios",
                "registro": item
            })
            continue

        # Validamos estado
        if estado not in ["ACTIVO", "INACTIVO"]:
            errores.append({
                "index": index,
                "error": "Estado no válido",
                "registro": item
            })
            continue

        # Creamos el paciente
        patient = Patient(
            nombre=nombre,
            telefono=telefono,
            id_usuario=id_usuario,
            estado=estado
        )

        db.session.add(patient)
        pacientes_creados.append(patient)

    # Guardamos todos los pacientes válidos
    db.session.commit()

    return jsonify({
        "message": "Carga masiva de pacientes procesada",
        "creados": len(pacientes_creados),
        "errores": len(errores),
        "patients": [patient.to_dict() for patient in pacientes_creados],
        "detalle_errores": errores
    }), 201

@admin_bp.route("/admin/doctores/bulk", methods=["POST"])
@roles_required("admin", "secretaria")
def create_doctors_bulk():
    # Recibimos una lista de doctores en formato JSON
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({
            "error": "Se esperaba una lista JSON de doctores"
        }), 400

    doctores_creados = []
    errores = []

    for index, item in enumerate(data):
        # Extraemos los campos de cada doctor
        nombre = item.get("nombre")
        especialidad = item.get("especialidad")
        id_usuario = item.get("id_usuario")
        estado = item.get("estado", "ACTIVO")

        # Validamos campos obligatorios
        if not nombre or not especialidad:
            errores.append({
                "index": index,
                "error": "Los campos nombre y especialidad son obligatorios",
                "registro": item
            })
            continue

        # Validamos estado
        if estado not in ["ACTIVO", "INACTIVO"]:
            errores.append({
                "index": index,
                "error": "Estado no válido",
                "registro": item
            })
            continue

        # Creamos el doctor
        doctor = Doctor(
            nombre=nombre,
            especialidad=especialidad,
            id_usuario=id_usuario,
            estado=estado
        )

        db.session.add(doctor)
        doctores_creados.append(doctor)

    # Guardamos todos los doctores válidos
    db.session.commit()

    return jsonify({
        "message": "Carga masiva de doctores procesada",
        "creados": len(doctores_creados),
        "errores": len(errores),
        "doctors": [doctor.to_dict() for doctor in doctores_creados],
        "detalle_errores": errores
    }), 201

@admin_bp.route("/admin/clinicas/bulk", methods=["POST"])
@roles_required("admin", "secretaria")
def create_clinics_bulk():
    # Recibimos una lista de clínicas en formato JSON
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({
            "error": "Se esperaba una lista JSON de clínicas"
        }), 400

    clinicas_creadas = []
    errores = []

    for index, item in enumerate(data):
        # Extraemos los campos de cada clínica
        nombre = item.get("nombre")
        direccion = item.get("direccion")
        estado = item.get("estado", "ACTIVO")

        # Validamos campos obligatorios
        if not nombre or not direccion:
            errores.append({
                "index": index,
                "error": "Los campos nombre y direccion son obligatorios",
                "registro": item
            })
            continue

        # Validamos estado
        if estado not in ["ACTIVO", "INACTIVO"]:
            errores.append({
                "index": index,
                "error": "Estado no válido",
                "registro": item
            })
            continue

        # Creamos la clínica
        clinic = Clinica(
            nombre=nombre,
            direccion=direccion,
            estado=estado
        )

        db.session.add(clinic)
        clinicas_creadas.append(clinic)

    # Guardamos todas las clínicas válidas
    db.session.commit()

    return jsonify({
        "message": "Carga masiva de clínicas procesada",
        "creados": len(clinicas_creadas),
        "errores": len(errores),
        "clinics": [clinic.to_dict() for clinic in clinicas_creadas],
        "detalle_errores": errores
    }), 201