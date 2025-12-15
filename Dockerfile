# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos e instalar librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la carpeta de scripts y el entrypoint
COPY scripts/ ./scripts/
COPY entrypoint.sh .

# Dar permisos de ejecución al script de entrada
RUN chmod +x entrypoint.sh

# Comando por defecto al iniciar el contenedor
ENTRYPOINT ["./entrypoint.sh"]