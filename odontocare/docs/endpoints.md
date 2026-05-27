# Documentación básica de endpoints - OdontoCare

## Descripción General

OdontoCare es una aplicación basada en arquitectura de microservicios para la gestión de un grupo de clínicas odontológicas.

Microservicios implementados:

- usuarios
- administracion
- citas
- api_gateway

La comunicación entre servicios se realiza mediante REST APIs y JWT.


# =========================================
# AUTENTICACIÓN
# =========================================

## POST /api/auth/register

Descripción:
Registra un nuevo usuario.

Endpoint:

```text
POST /api/auth/register
```

JSON de entrada:

```json
{
  "username": "admin1",
  "email": "admin1@odontocare.com",
  "password": "123456",
  "role": "admin"
}
```

Respuesta esperada:

```json
{
  "message": "Usuario registrado correctamente"
}
```


## POST /api/auth/login

Descripción:
Inicia sesión y devuelve un token JWT.

Endpoint:

```text
POST /api/auth/login
```

JSON de entrada:

```json
{
  "email": "admin1@odontocare.com",
  "password": "123456"
}
```

Respuesta esperada:

```json
{
  "message": "Inicio de sesión correcto",
  "token": "JWT_TOKEN"
}
```


# =========================================
# ADMINISTRACIÓN
# =========================================

## POST /api/admin/pacientes

Descripción:
Crea un paciente.

Endpoint:

```text
POST /api/admin/pacientes
```

JSON de entrada:

```json
{
  "id_usuario": 1,
  "nombre": "Paciente Demo",
  "telefono": "+34600111222",
  "estado": "ACTIVO"
}
```


## GET /api/admin/pacientes

Descripción:
Lista todos los pacientes registrados permitiendo paginación de los resultados.

Endpoint:

```text
GET /api/admin/pacientes
```


## POST /api/admin/doctores

Descripción:
Crea un doctor.

Endpoint:

```text
POST /api/admin/doctores
```

JSON de entrada:

```json
{
  "id_usuario": 2,
  "nombre": "Dra. Laura Sánchez",
  "especialidad": "Ortodoncia",
  "estado": "ACTIVO"
}
```


## GET /api/admin/doctores

Descripción:
Lista todos los doctores registrados permitiendo paginación de los resultados.

Endpoint:

```text
GET /api/admin/doctores
```


## POST /api/admin/clinicas

Descripción:
Crea una clínica.

Endpoint:

```text
POST /api/admin/clinicas
```

JSON de entrada:

```json
{
  "nombre": "Clínica Central",
  "direccion": "Calle Mayor 10",
  "estado": "ACTIVO"
}
```


## GET /api/admin/clinicas

Descripción:
Lista todas las clínicas registradas permitiendo paginación de los resultados.

Endpoint:

```text
GET /api/admin/clinicas
```


# =========================================
# CITAS
# =========================================

## POST /api/citas

Descripción:
Crea una cita médica.

Endpoint:

```text
POST /api/citas
```

JSON de entrada:

```json
{
  "id_paciente": 1,
  "id_doctor": 6,
  "id_clinica": 1,
  "fecha_hora": "2026-06-10 10:00",
  "motivo": "Revisión general",
  "estado": "PROGRAMADA"
}
```

Validaciones implementadas:

- existencia de paciente
- existencia de doctor
- existencia de clínica
- conflicto horario de doctor
- conflicto horario de clínica


## GET /api/citas

Descripción:
Lista citas registradas permitiendo paginación de los resultados.

Endpoint:

```text
GET /api/citas
```

Filtros disponibles mediante query params:

```text
id_doctor
id_clinica
id_paciente
fecha
estado
```

Ejemplo:

```bash
curl "http://localhost:5000/api/citas?id_doctor=6" \
-H "Authorization: Bearer TOKEN"
```


# =========================================
# CARGA MASIVA CSV
# =========================================

## Script: carga_inicial.py

Descripción:

El script:

1. Realiza login con usuario administrador.
2. Procesa el archivo datos.csv.
3. Envía registros a la API.
4. Crea una cita médica.
5. Imprime el JSON de la cita creada.

Ejemplo de ejecución:

```bash
python scripts/carga_inicial.py \
data/datos.csv \
http://localhost:5000
```


## Archivo: datos.csv

Ejemplo:

```csv
tipo,username,email,password,role,id_usuario,nombre,telefono,especialidad,direccion,estado
usuario,admin_csv,admin_csv@odontocare.com,123456,admin,,,,,,ACTIVO
paciente,,,,,100,Paciente CSV 1,+34600111111,,,ACTIVO
doctor,,,,,200,Dr. CSV 1,,Ortodoncia,,ACTIVO
clinica,,,,,,Clínica CSV 1,,,Calle Mayor 10,ACTIVO
```


# =========================================
# PRUEBAS DE INTEGRACIÓN
# =========================================

## Script: test_integracion.sh

Descripción:

Realiza pruebas automáticas de:

- health checks
- login
- acceso autenticado
- consulta de recursos
- creación de citas
- validación de conflictos horarios

Ejemplo de ejecución:

```bash
bash scripts/test_integracion.sh
```


# =========================================
# TECNOLOGÍAS UTILIZADAS
# =========================================

- Python
- Flask
- SQLAlchemy
- SQLite
- JWT
- Docker
- Docker Compose
- REST APIs
