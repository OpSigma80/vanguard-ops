# Usamos una versión ligera de Python
FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos las dependencias de Linux necesarias para Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Instalamos las librerías de Python directamente aquí para asegurar que se instalen
RUN pip install --no-cache-dir fastapi uvicorn pydantic[email] python-dotenv psycopg[binary] jinja2 pytest httpx

# Copiamos todo tu código
COPY . .

# El comando para arrancar (ajustado a tu carpeta)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]