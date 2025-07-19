#!/bin/bash

# --- Script de Despliegue para el Servidor ---

# Detener la ejecución inmediatamente si un comando falla
set -e

# El directorio donde se encuentra tu docker-compose.yml en el servidor
PROJECT_DIR="/home/opc/app-personal-finance-backend" # <-- ¡IMPORTANTE! Cambia esto a la ruta real en tu servidor Oracle

# Navegar al directorio del proyecto
cd $PROJECT_DIR

echo "Navegando a $PROJECT_DIR"

# Descargar la última imagen de Docker para el servicio 'backend'
# Docker Compose buscará la imagen especificada en docker-compose.yml
echo "Descargando la última imagen de Docker..."
docker-compose pull backend

# Reiniciar el servicio 'backend' usando la nueva imagen
# -d: modo detached (corre en segundo plano)
# --no-deps: no reinicia las dependencias (si las hubiera)
# --build: opcional, si necesitaras construir la imagen en el servidor
echo "Reiniciando el servicio backend..."
docker-compose up -d --no-deps backend

echo "✅ ¡Despliegue completado exitosamente!"
