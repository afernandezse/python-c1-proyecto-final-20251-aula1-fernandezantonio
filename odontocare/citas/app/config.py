class Config:
    # Base de datos SQLite persistente dentro del volumen Docker
    SQLALCHEMY_DATABASE_URI = "sqlite:////app/db/citas.db"

    # Desactivamos el seguimiento de modificaciones para evitar sobrecarga
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Clave usada para validar tokens JWT recibidos desde el servicio usuarios
    JWT_SECRET_KEY = "clave-secreta-desarrollo"

    # URL interna del microservicio de administración dentro de Docker Compose
    ADMIN_SERVICE_URL = "http://administracion:5000"