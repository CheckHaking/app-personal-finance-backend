#!/bin/bash

# Script para ejecutar las pruebas del proyecto Personal Finance

echo "🧪 Ejecutando pruebas del proyecto Personal Finance..."
echo "=================================================="

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  No se detectó un entorno virtual activo${NC}"
    echo "Activando entorno virtual..."
    source venv/bin/activate 2>/dev/null || {
        echo -e "${RED}❌ No se pudo activar el entorno virtual${NC}"
        echo "Crea uno con: python -m venv venv"
        exit 1
    }
fi

# Instalar dependencias de test si no están instaladas
echo "📦 Verificando dependencias de testing..."
pip install -q -r requirements-test.txt 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Instalando dependencias de testing...${NC}"
    pip install -r requirements-test.txt
}

# Limpiar caché de pytest
echo "🧹 Limpiando caché..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Opciones de pytest
PYTEST_OPTIONS="-v"

# Agregar opciones según argumentos
if [ "$1" == "coverage" ]; then
    echo "📊 Ejecutando con cobertura de código..."
    PYTEST_OPTIONS="$PYTEST_OPTIONS --cov --cov-report=html --cov-report=term"
elif [ "$1" == "fast" ]; then
    echo "⚡ Ejecutando pruebas rápidas (sin pruebas lentas)..."
    PYTEST_OPTIONS="$PYTEST_OPTIONS -m 'not slow'"
elif [ "$1" == "parallel" ]; then
    echo "🚀 Ejecutando pruebas en paralelo..."
    PYTEST_OPTIONS="$PYTEST_OPTIONS -n auto"
fi

# Ejecutar migraciones de prueba
echo "🗄️  Preparando base de datos de prueba..."
python manage.py migrate --run-syncdb 2>/dev/null

# Ejecutar pruebas
echo ""
echo "🏃 Ejecutando pruebas..."
echo "========================"

# Ejecutar pytest
pytest $PYTEST_OPTIONS $2 $3 $4

# Capturar código de salida
EXIT_CODE=$?

# Mostrar resumen
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ¡Todas las pruebas pasaron exitosamente!${NC}"
    
    # Si se ejecutó con coverage, mostrar ubicación del reporte
    if [[ "$1" == "coverage" ]]; then
        echo ""
        echo "📊 Reporte de cobertura generado en: htmlcov/index.html"
        echo "   Ábrelo con: open htmlcov/index.html"
    fi
else
    echo -e "${RED}❌ Algunas pruebas fallaron${NC}"
fi

echo ""
echo "Uso del script:"
echo "  ./run_tests.sh              # Ejecutar todas las pruebas"
echo "  ./run_tests.sh coverage     # Con reporte de cobertura"
echo "  ./run_tests.sh fast         # Solo pruebas rápidas"
echo "  ./run_tests.sh parallel     # En paralelo (más rápido)"
echo ""
echo "También puedes especificar archivos específicos:"
echo "  ./run_tests.sh normal core/tests/test_models_complete.py"

exit $EXIT_CODE