class Config:
    # URLs internas de los microservicios dentro de Docker Compose
    USUARIOS_SERVICE_URL = "http://usuarios:5000"
    ADMIN_SERVICE_URL = "http://administracion:5000"
    CITAS_SERVICE_URL = "http://citas:5000"