from datetime import datetime, timezone
from app.extensions import db


class Cita(db.Model):

    __tablename__ = "citas"

    # Identificador interno de la cita
    id = db.Column(db.Integer, primary_key=True)

    # Identificadores de otros microservicios.
    # No usamos ForeignKey porque cada microservicio tiene su propia base de datos.
    id_paciente = db.Column(db.Integer, nullable=False)
    id_doctor = db.Column(db.Integer, nullable=False)
    id_clinica = db.Column(db.Integer, nullable=False)

    # Fecha y hora de la cita en formato ISO: YYYY-MM-DD HH:MM
    fecha_hora = db.Column(db.DateTime, nullable=False)

    # Motivo de la consulta
    motivo = db.Column(db.String(250), nullable=True)

    # Estado operativo de la cita
    # Valores esperados: PROGRAMADA / COMPLETADA / CANCELADA
    estado = db.Column(db.String(20), nullable=False, default="PROGRAMADA")

    # Fecha de creación del registro
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        # Convertimos el objeto Cita a diccionario para responder en JSON
        return {
            "id": self.id,
            "id_paciente": self.id_paciente,
            "id_doctor": self.id_doctor,
            "id_clinica": self.id_clinica,
            "fecha_hora": self.fecha_hora.isoformat(),
            "motivo": self.motivo,
            "estado": self.estado,
            "created_at": self.created_at.isoformat()
        }
