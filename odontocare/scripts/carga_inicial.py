import csv
import sys
import json
import requests


def leer_csv(archivo_csv):
    # Leemos el CSV local y detectamos separador: coma, tabulador o punto y coma
    with open(archivo_csv, newline="", encoding="utf-8") as csvfile:
        muestra = csvfile.read(1024)
        csvfile.seek(0)
        dialect = csv.Sniffer().sniff(muestra, delimiters=",\t;")
        reader = csv.DictReader(csvfile, dialect=dialect)
        return list(reader)


def registrar_admin(url_base_api, admin):
    # Registramos el usuario admin indicado en datos.csv si no existe
    response = requests.post(
        f"{url_base_api}/api/auth/register",
        json={
            "username": admin["username"],
            "email": admin["email"],
            "password": admin["password"],
            "role": "admin"
        },
        timeout=10
    )

    if response.status_code not in [201, 409]:
        print(f"[AVISO] No se pudo registrar el admin: {response.text}")


def login_admin(url_base_api, admin):
    # Hacemos login con el admin del CSV
    response = requests.post(
        f"{url_base_api}/api/auth/login",
        json={
            "email": admin["email"],
            "password": admin["password"]
        },
        timeout=10
    )

    response.raise_for_status()
    return response.json()["token"]


def construir_payload(row):
    # Creamos el JSON adecuado según el tipo de entidad
    tipo = row.get("tipo")

    if tipo == "paciente":
        return "/api/admin/pacientes", {
            "id_usuario": int(row["id_usuario"]),
            "nombre": row["nombre"],
            "telefono": row["telefono"],
            "estado": row.get("estado", "ACTIVO")
        }

    if tipo == "doctor":
        return "/api/admin/doctores", {
            "id_usuario": int(row["id_usuario"]),
            "nombre": row["nombre"],
            "especialidad": row["especialidad"],
            "estado": row.get("estado", "ACTIVO")
        }

    if tipo == "clinica":
        return "/api/admin/clinicas", {
            "nombre": row["nombre"],
            "direccion": row["direccion"],
            "estado": row.get("estado", "ACTIVO")
        }

    return None, None


def enviar_registros(filas, token, url_base_api):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    creados = 0
    errores = 0

    # Guardamos los primeros IDs creados para usarlos al crear la cita
    ids_creados = {
        "paciente": None,
        "doctor": None,
        "clinica": None
    }

    for index, row in enumerate(filas):
        if row.get("tipo") == "usuario":
            continue

        endpoint, payload = construir_payload(row)

        if endpoint is None:
            errores += 1
            print(f"[ERROR] Registro {index}: tipo no reconocido -> {row}")
            continue

        response = requests.post(
            f"{url_base_api}{endpoint}",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            creados += 1
            respuesta_json = response.json()

            if row["tipo"] == "paciente" and ids_creados["paciente"] is None:
                ids_creados["paciente"] = respuesta_json["patient"]["id_paciente"]

            if row["tipo"] == "doctor" and ids_creados["doctor"] is None:
                ids_creados["doctor"] = respuesta_json["doctor"]["id"]

            if row["tipo"] == "clinica" and ids_creados["clinica"] is None:
                ids_creados["clinica"] = respuesta_json["clinic"]["id"]

            print(f"[OK] Registro {index} creado correctamente ({row['tipo']})")

        else:
            errores += 1
            print(f"[ERROR] Registro {index}: {response.text}")

    print("\nResumen carga de datos")
    print(f"Registros creados: {creados}")
    print(f"Errores: {errores}")

    return ids_creados


def crear_cita(url_base_api, token, id_paciente, id_doctor, id_clinica):
    # Creamos una cita médica usando IDs reales devueltos por la API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f"{url_base_api}/api/citas",
        json={
            "id_paciente": id_paciente,
            "id_doctor": id_doctor,
            "id_clinica": id_clinica,
            "fecha_hora": "2026-06-01 10:00",
            "motivo": "Cita creada desde carga_inicial.py",
            "estado": "PROGRAMADA"
        },
        headers=headers,
        timeout=10
    )

    if response.status_code != 201:
        print("[ERROR] No se pudo crear la cita:")
        print(response.text)
        response.raise_for_status()

    return response.json()


def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/carga_inicial.py <datos.csv> <url_base_api>")
        sys.exit(1)

    archivo_csv = sys.argv[1]
    url_base_api = sys.argv[2].rstrip("/")

    filas = leer_csv(archivo_csv)

    admin = next(
        (row for row in filas if row.get("tipo") == "usuario" and row.get("role") == "admin"),
        None
    )

    if not admin:
        print("No se encontró usuario admin en datos.csv")
        sys.exit(1)

    registrar_admin(url_base_api, admin)
    token = login_admin(url_base_api, admin)

    ids_creados = enviar_registros(filas, token, url_base_api)

    if not all(ids_creados.values()):
        print("[ERROR] No se pudieron obtener IDs suficientes para crear la cita")
        print(ids_creados)
        sys.exit(1)

    cita = crear_cita(
        url_base_api,
        token,
        ids_creados["paciente"],
        ids_creados["doctor"],
        ids_creados["clinica"]
    )

    print("\nJSON de la cita creada:")
    print(json.dumps(cita, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()