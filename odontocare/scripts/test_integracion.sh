#!/usr/bin/env bash

set -euo pipefail

API_URL="http://localhost:5000"

ADMIN_EMAIL="antonio@example.com"
ADMIN_PASSWORD="123456"

echo "== Test de integración OdontoCare =="

echo
echo "1. Comprobando API Gateway..."
curl -s "${API_URL}/health" | jq

echo
echo "2. Login como admin..."
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

echo
echo "3. Consultando pacientes vía API Gateway..."
curl -s "${API_URL}/api/admin/pacientes" \
  -H "Authorization: Bearer ${TOKEN}" | jq

echo
echo "4. Consultando doctores vía API Gateway..."
curl -s "${API_URL}/api/admin/doctores" \
  -H "Authorization: Bearer ${TOKEN}" | jq

echo
echo "5. Consultando clínicas vía API Gateway..."
curl -s "${API_URL}/api/admin/clinicas" \
  -H "Authorization: Bearer ${TOKEN}" | jq

echo
echo "6. Creando cita de prueba..."
CITA_RESPONSE=$(curl -s -X POST "${API_URL}/api/citas" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "id_paciente": 1,
    "id_doctor": 6,
    "id_clinica": 1,
    "fecha_hora": "2026-06-10 10:00",
    "motivo": "Cita creada desde test_integracion.sh",
    "estado": "PROGRAMADA"
  }')

echo "${CITA_RESPONSE}" | jq

echo
echo "7. Probando conflicto horario para el mismo doctor..."
CONFLICTO_RESPONSE=$(curl -s -X POST "${API_URL}/api/citas" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "id_paciente": 1,
    "id_doctor": 6,
    "id_clinica": 1,
    "fecha_hora": "2026-06-10 10:00",
    "motivo": "Conflicto esperado",
    "estado": "PROGRAMADA"
  }')

echo "${CONFLICTO_RESPONSE}" | jq

echo
echo "8. Listando citas filtradas por doctor..."
curl -s "${API_URL}/api/citas?id_doctor=6" \
  -H "Authorization: Bearer ${TOKEN}" | jq

echo
echo "== Test de integración finalizado =="