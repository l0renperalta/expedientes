# Usa la imagen base de Alpine con soporte para Python
FROM python:3.11.4-alpine

# Establece el directorio de trabajo en /app
WORKDIR /app

# Instala dependencias necesarias
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    bash \
    antiword \
    && pip install --no-cache-dir --upgrade pip

# Copia los archivos de tu aplicación al contenedor
COPY . /app

# Instala las dependencias de tu aplicación
RUN pip install --no-cache-dir -r requirements.txt

# Especifica el comando a ejecutar cuando se inicie el contenedor
CMD ["python", "app.py"]