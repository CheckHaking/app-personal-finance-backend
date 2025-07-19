# 1. Usar una imagen base oficial de Python
FROM python:3.10-slim

# 2. Evitar que Python escriba archivos .pyc y mantener los logs fluyendo
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalar las dependencias
# Copiar solo el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código de la aplicación al directorio de trabajo
COPY . .

# 6. Exponer el puerto en el que correrá la aplicación
EXPOSE 8000

# 7. Comando para ejecutar la aplicación en producción usando Gunicorn
# Asegúrate de que 'config.wsgi:application' coincida con la estructura de tu proyecto
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
