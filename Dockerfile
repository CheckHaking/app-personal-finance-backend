FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dos2unix para convertir CRLF→LF
RUN apt-get update \
 && apt-get install -y --no-install-recommends dos2unix \
 && rm -rf /var/lib/apt/lists/*

# Copia y convierte requisitos
COPY requirements.txt .
RUN dos2unix requirements.txt \
 && pip install --no-cache-dir -r requirements.txt

# Copia el resto del código y convierte todos los ficheros
COPY . .
RUN find . -type f -exec dos2unix {} \;

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
