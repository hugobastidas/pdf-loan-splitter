#!/bin/bash
# Script de verificación de configuración del sistema

set -e

echo "======================================"
echo "  PDF Classifier - Verificación"
echo "======================================"
echo ""

ERRORS=0

# Función para verificar comandos
check_command() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1 encontrado: $(command -v $1)"
        if [ ! -z "$2" ]; then
            echo "  Versión: $($1 $2 2>&1 | head -n1)"
        fi
    else
        echo "✗ $1 NO encontrado"
        ERRORS=$((ERRORS + 1))
    fi
}

# Verificar Docker
echo "=== Verificando Docker ==="
check_command docker "--version"
echo ""

# Verificar Docker Compose
echo "=== Verificando Docker Compose ==="
check_command docker-compose "--version"
echo ""

# Verificar estructura de directorios
echo "=== Verificando estructura de directorios ==="
REQUIRED_DIRS=(
    "backend/app"
    "backend/app/api"
    "backend/app/core"
    "backend/app/db"
    "backend/app/workers"
    "storage/input"
    "storage/output"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir existe"
    else
        echo "✗ $dir NO existe"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Verificar archivos requeridos
echo "=== Verificando archivos requeridos ==="
REQUIRED_FILES=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/Dockerfile.worker"
    "backend/requirements.txt"
    "backend/app/main.py"
    "backend/app/config.py"
    "backend/app/core/pdf_processor.py"
    "backend/app/workers/worker.py"
    ".env.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file existe"
    else
        echo "✗ $file NO existe"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Verificar archivo .env
echo "=== Verificando configuración ==="
if [ -f ".env" ]; then
    echo "✓ .env existe"
else
    echo "⚠ .env NO existe (usando valores por defecto de docker-compose.yml)"
    echo "  Puedes crear uno con: cp .env.example .env"
fi
echo ""

# Verificar servicios Docker (si están corriendo)
echo "=== Verificando servicios Docker ==="
if docker-compose ps &> /dev/null; then
    echo "Servicios en ejecución:"
    docker-compose ps
else
    echo "ℹ No hay servicios corriendo actualmente"
    echo "  Iniciar con: make up o docker-compose up -d"
fi
echo ""

# Resumen
echo "======================================"
if [ $ERRORS -eq 0 ]; then
    echo "✓ Verificación completada: TODO OK"
    echo ""
    echo "Siguientes pasos:"
    echo "  1. make build    # Construir imágenes"
    echo "  2. make up       # Iniciar servicios"
    echo "  3. make logs     # Ver logs"
    echo "  4. ./test_api.sh # Probar API"
else
    echo "✗ Verificación completada con $ERRORS errores"
    echo "Por favor, revisa los errores arriba"
fi
echo "======================================"
