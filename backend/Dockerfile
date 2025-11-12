# Dockerfile optimizado para PDF Classifier Backend
FROM python:3.11-slim

# Metadatos
LABEL maintainer="PDF Classifier Team"
LABEL version="1.0.0"
LABEL description="Backend para clasificación de PDFs con OCR y códigos de barras"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIPENV_VENV_IN_PROJECT=1 \
    PIPENV_CUSTOM_VENV_NAME=.venv

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-spa \
    # Librerías para procesamiento de imágenes
    libzbar0 \
    poppler-utils \
    # Librerías de OpenCV
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    # Utilidades
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Instalar pipenv
RUN pip install --upgrade pip setuptools wheel && \
    pip install pipenv

# Copiar Pipfile y Pipfile.lock
COPY Pipfile Pipfile.lock* ./

# Instalar dependencias con pipenv
RUN pipenv install --system --deploy --ignore-pipfile

# Copiar código de la aplicación
COPY app/ ./app/

# Crear directorios de almacenamiento
RUN mkdir -p /app/storage/input /app/storage/output

# Exponer puerto
EXPOSE 8000

# Usuario no privilegiado (seguridad)
RUN useradd -m -u 1000 pdfuser && \
    chown -R pdfuser:pdfuser /app

USER pdfuser

# Comando por defecto (API)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
