from datetime import datetime, timezone
from app.extensions import db

class Patient(db.Model):

    __tablename__ = "patients"

    id_paciente = db.Column(db.Integer, primary_key = True)
    # Identificador del usuario asociado en el microservicio de usuarios
    # No se declara ForeignKey real porque los microservicios no comparten base de datos
    id_usuario = db.Column(db.Integer, nullable=True)

    nombre = db.Column(db.String(80), nullable = False)
    telefono = db.Column(db.String(30), nullable = False)
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")


    # Fecha de creación del registro
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )



    def to_dict(self):
        # Convertimos el objeto Patient a diccionario para devolverlo como JSON
        return {
            "id_paciente": self.id_paciente,
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "estado": self.estado,
            "created_at": self.created_at.isoformat()
        }
    
class Doctor(db.Model):
    __tablename__ = "doctors"

    # Identificador interno del doctor
    id = db.Column(db.Integer, primary_key=True)

    # Identificador del usuario asociado en el microservicio usuarios
    id_usuario = db.Column(db.Integer, nullable=True)

    nombre = db.Column(db.String(80), nullable=False)
    especialidad = db.Column(db.String(120), nullable=False)

    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        # Convertimos el objeto Doctor a diccionario para responder en JSON
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "especialidad": self.especialidad,
            "estado": self.estado,
            "created_at": self.created_at.isoformat()
        }
    
class Clinica(db.Model):
    __tablename__ = "clinicas"

    # Identificador interno de la clínica
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    # Estado operativo de la clínica, coherencia con los demás modelos
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        # Convertimos el objeto Clínica a diccionario para responder en JSON
        return {
            "id": self.id,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "created_at": self.created_at.isoformat()
        }

