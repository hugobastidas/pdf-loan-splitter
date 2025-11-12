#!/bin/bash
# Script de prueba de la API PDF Classifier

set -e

API_URL="http://localhost:8000"
TEST_PDF="test_document.pdf"

echo "======================================"
echo "  PDF Classifier API - Test Script"
echo "======================================"
echo ""

# Test 1: Health check
echo "1. Verificando health check..."
curl -s "${API_URL}/health" | python3 -m json.tool
echo ""

# Test 2: Root endpoint
echo "2. Verificando endpoint raíz..."
curl -s "${API_URL}/" | python3 -m json.tool
echo ""

# Test 3: Upload (requiere archivo PDF)
if [ -f "$TEST_PDF" ]; then
    echo "3. Subiendo PDF de prueba: $TEST_PDF"
    RESPONSE=$(curl -s -X POST "${API_URL}/api/upload" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@${TEST_PDF}")

    echo "$RESPONSE" | python3 -m json.tool

    # Extraer job_id
    JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")

    if [ -n "$JOB_ID" ]; then
        echo ""
        echo "Job ID: $JOB_ID"

        # Test 4: Consultar estado del job
        echo ""
        echo "4. Consultando estado del job..."
        sleep 2
        curl -s "${API_URL}/api/jobs/${JOB_ID}" | python3 -m json.tool

        # Test 5: Esperar y consultar logs
        echo ""
        echo "5. Esperando procesamiento (15 segundos)..."
        sleep 15

        echo ""
        echo "6. Consultando logs del job..."
        curl -s "${API_URL}/api/jobs/${JOB_ID}/logs" | python3 -m json.tool

        echo ""
        echo "7. Consultando estado final del job..."
        curl -s "${API_URL}/api/jobs/${JOB_ID}" | python3 -m json.tool

        # Test 6: Listar documentos
        echo ""
        echo "8. Listando documentos procesados..."
        curl -s "${API_URL}/api/documents?job_id=${JOB_ID}" | python3 -m json.tool
    fi
else
    echo "3. SKIP: No se encontró archivo de prueba $TEST_PDF"
    echo "   Para probar upload, coloca un PDF en este directorio con el nombre $TEST_PDF"
fi

# Test 7: Listar todos los jobs
echo ""
echo "9. Listando todos los jobs..."
curl -s "${API_URL}/api/jobs?limit=5" | python3 -m json.tool

echo ""
echo "======================================"
echo "  Tests completados"
echo "======================================"
