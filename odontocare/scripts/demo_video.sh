#!/usr/bin/env bash

set -uo pipefail

API_URL="http://localhost:5000"

ADMIN_EMAIL="antonio@example.com"
ADMIN_PASSWORD="123456"

pausa() {
  echo
  read -r -p "Pulsa ENTER para continuar..."
}

echo
#echo "===== ODONTOCARE DEMO =====" | lolcat -a
# toilet -f future "ODONTOCARE DEMO" | lolcat -a
figlet "ODONTOCARE DEMO" | lolcat -a
pausa

echo
echo ">>> Estado de contenedores" | lolcat -a
docker-compose ps
pausa

echo
echo ">>> Health checks de todos los microservicios" | lolcat -a

echo 'GET /health - Administración'
curl -s "http://localhost:5002/health" | jq
pausa

echo 'GET /health - API Gateway'
curl -s "${API_URL}/health" | jq
pausa

echo 'GET /health - Citas'
curl -s "http://localhost:5003/health" | jq
pausa

echo 'GET /health - Usuarios'
curl -s "http://localhost:5001/health" | jq
pausa


echo
echo ">>> Login administrador" | lolcat -a
echo 'POST /api/auth/login'

LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/login" \
-H "Content-Type: application/json" \
-d "{
  \"email\": \"${ADMIN_EMAIL}\",
  \"password\": \"${ADMIN_PASSWORD}\"
}")

echo "${LOGIN_RESPONSE}" | jq

TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.token')

if [[ "${TOKEN}" == "null" || -z "${TOKEN}" ]]; then
  echo "[ERROR] No se pudo obtener token JWT"
  exit 1
fi

pausa

echo
echo ">>> Demostración CRUD de pacientes" | lolcat -a

echo
echo "CREATE - POST /api/admin/pacientes"

CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/pacientes" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${TOKEN}" \
-d '{
  "nombre": "Paciente Demo CRUD",
  "telefono": "+34600777888",
  "estado": "ACTIVO"
}')

echo "${CREATE_RESPONSE}" | jq

PACIENTE_ID=$(echo "${CREATE_RESPONSE}" | jq -r '.patient.id_paciente')

pausa

echo
echo "READ - GET /api/admin/pacientes/{id}"

curl -s "${API_URL}/api/admin/pacientes/${PACIENTE_ID}" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo "UPDATE - PUT /api/admin/pacientes/{id}"

curl -s -X PUT "${API_URL}/api/admin/pacientes/${PACIENTE_ID}" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${TOKEN}" \
-d '{
  "nombre": "Paciente Demo CRUD Actualizado",
  "telefono": "+34600777999",
  "estado": "ACTIVO"
}' | jq

pausa

echo
echo "DELETE - DELETE /api/admin/pacientes/{id}"

curl -s -X DELETE "${API_URL}/api/admin/pacientes/${PACIENTE_ID}" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo "READ tras DELETE - debe devolver Paciente no encontrado"

curl -s "${API_URL}/api/admin/pacientes/${PACIENTE_ID}" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo ">>> Carga inicial desde CSV" | lolcat -a
echo 'python carga_inicial.py ../../data/datos_carga.csv http://localhost:5000'

python carga_inicial.py \
../../data/datos_carga.csv \
"${API_URL}"

pausa

echo
echo ">>> Pacientes paginados" | lolcat -a
echo 'GET /api/admin/pacientes?page=1&per_page=2'

curl -s "${API_URL}/api/admin/pacientes?page=1&per_page=2" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo 
echo ">>> Doctores paginados" | lolcat -a
echo 'GET /api/admin/doctores?page=1&per_page=2'

curl -s "${API_URL}/api/admin/doctores?page=1&per_page=2" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo ">>> Clínicas paginadas" | lolcat -a
echo 'GET /api/admin/clinicas?page=1&per_page=2'

curl -s "${API_URL}/api/admin/clinicas?page=1&per_page=2" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo ">>> Citas filtradas por doctor" | lolcat -a
echo 'GET /api/citas?id_doctor=6&page=1&per_page=2'

curl -s "${API_URL}/api/citas?id_doctor=6&page=1&per_page=2" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
echo ">>> Carga masiva JSON" | lolcat -a
echo 'POST /api/admin/pacientes/bulk'

curl -s -X POST "${API_URL}/api/admin/pacientes/bulk" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${TOKEN}" \
-d '[
  {
    "nombre": "Paciente Bulk Demo 1",
    "telefono": "+34600999111",
    "estado": "ACTIVO"
  },
  {
    "nombre": "Paciente Bulk Demo 2",
    "telefono": "+34600999222",
    "estado": "ACTIVO"
  }
]' | jq

pausa

echo
echo ">>> Validación de conflicto horario" | lolcat -a
echo 'POST /api/citas con doctor 6, clínica 1 y fecha ya ocupada'

curl -s -X POST "${API_URL}/api/citas" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${TOKEN}" \
-d '{
  "id_paciente": 1,
  "id_doctor": 6,
  "id_clinica": 1,
  "fecha_hora": "2026-05-26 10:00",
  "motivo": "Conflicto esperado",
  "estado": "PROGRAMADA"
}' | jq

pausa

echo
echo ">>> Prueba de integración simplificada" | lolcat -a

echo "El proyecto incluye el script:"
echo "bash scripts/test_integracion.sh"

pausa

echo
echo "Comprobación breve de integración vía API Gateway:"
echo 'GET /api/citas?id_doctor=6&page=1&per_page=2'

curl -s "${API_URL}/api/citas?id_doctor=6&page=1&per_page=2" \
-H "Authorization: Bearer ${TOKEN}" | jq

pausa

echo
toilet -f future "===== FIN DEMO =====" | lolcat -a
