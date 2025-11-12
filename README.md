# PDF Classifier App - Backend

Backend completo y local para procesamiento, clasificación y división de archivos PDF basados en páginas separadoras con códigos de barras.

## Características

- **Procesamiento Asíncrono**: Utiliza Redis + RQ para procesamiento en background
- **OCR en Español**: Tesseract OCR configurado para español
- **Detección de Códigos de Barras**: Usando pyzbar/zbar
- **Eliminación de Páginas en Blanco**: Detección automática con umbral configurable
- **División Inteligente**: Divide PDFs según páginas separadoras con códigos de barras
- **Clasificación Automática**: Clasifica documentos por tipo (cédula, certificado, etc.)
- **100% Local**: Sin dependencias en la nube
- **API REST**: FastAPI con documentación automática

## Arquitectura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ HTTP
┌──────▼──────────┐
│   FastAPI       │
│   (Backend)     │
└────┬───────┬────┘
     │       │
┌────▼─┐  ┌──▼────┐
│Redis │  │ PostgreSQL │
└────┬─┘  └───────┘
     │
┌────▼─────┐
│ RQ Worker│
│ (PDF     │
│ Processor)│
└──────────┘
```

## Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM mínimo (recomendado 8GB)
- 10GB espacio en disco

## Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd pdf-loan-splitter
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` según necesidades (opcional, los valores por defecto funcionan).

### 3. Construir e iniciar servicios

```bash
# Usando Makefile
make build
make up

# O directamente con docker-compose
docker-compose build
docker-compose up -d
```

### 4. Verificar estado

```bash
make status

# O
docker-compose ps
```

### 5. Ver logs

```bash
# Todos los servicios
make logs

# Solo API
make logs-api

# Solo worker
make logs-worker
```

## Uso de la API

La API estará disponible en `http://localhost:8000`

### Documentación Interactiva

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints Principales

#### 1. Subir PDF para procesamiento

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "job_id": "job_abc123def456",
  "filename": "documento.pdf",
  "status": "pending",
  "message": "Archivo subido exitosamente. Procesamiento iniciado.",
  "rq_job_id": "rq_xyz789"
}
```

#### 2. Consultar estado de un job

```bash
curl "http://localhost:8000/api/jobs/job_abc123def456"
```

**Respuesta:**
```json
{
  "job_id": "job_abc123def456",
  "filename": "documento.pdf",
  "status": "completed",
  "total_pages": 25,
  "processed_pages": 25,
  "documents_created": 5,
  "error_message": null,
  "processing_time": 12.34,
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:05",
  "completed_at": "2024-01-15T10:30:17"
}
```

#### 3. Listar documentos procesados

```bash
# Todos los documentos
curl "http://localhost:8000/api/documents"

# Filtrar por job
curl "http://localhost:8000/api/documents?job_id=job_abc123def456"

# Filtrar por tipo
curl "http://localhost:8000/api/documents?document_type=cedula"
```

#### 4. Descargar documento procesado

```bash
curl "http://localhost:8000/api/documents/1/download" -o documento.pdf
```

#### 5. Ver logs de un job

```bash
curl "http://localhost:8000/api/jobs/job_abc123def456/logs"
```

## Estructura del Proyecto

```
pdf-loan-splitter/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuración
│   │   ├── api/
│   │   │   ├── upload.py        # Endpoint de subida
│   │   │   ├── jobs.py          # Consulta de jobs
│   │   │   └── documents.py     # Consulta de documentos
│   │   ├── core/
│   │   │   ├── pdf_processor.py # Procesador principal
│   │   │   └── utils.py         # Utilidades
│   │   ├── workers/
│   │   │   └── worker.py        # Worker RQ
│   │   └── db/
│   │       ├── database.py      # Config DB
│   │       └── models.py        # Modelos SQLAlchemy
│   ├── Dockerfile               # Dockerfile del API
│   ├── Dockerfile.worker        # Dockerfile del worker
│   └── requirements.txt         # Dependencias Python
├── storage/
│   ├── input/                   # PDFs subidos
│   └── output/                  # PDFs procesados
├── docker-compose.yml           # Orquestación de servicios
├── Makefile                     # Comandos útiles
└── README.md                    # Este archivo
```

## Tipos de Documentos Soportados

El sistema clasifica automáticamente los siguientes tipos de documentos:

- `cedula`: Cédula de identidad
- `certificado`: Certificados generales
- `papeleta_votacion`: Papeleta de votación
- `mecanizado`: Planilla mecanizada IESS
- `planilla_servicios`: Planillas de servicios básicos
- `certificado_cuenta`: Certificado bancario
- `unknown`: No clasificado

## Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://pdfuser:pdfpass@db:5432/pdfdb` |
| `REDIS_URL` | URL de Redis | `redis://redis:6379/0` |
| `STORAGE_ROOT` | Directorio raíz de almacenamiento | `/app/storage` |
| `TIMEZONE` | Zona horaria | `America/Guayaquil` |
| `TESSERACT_LANG` | Idioma de Tesseract | `spa` |
| `BLANK_PAGE_THRESHOLD` | Umbral para detectar páginas en blanco | `0.98` |
| `PDF_DPI` | DPI para conversión de PDF a imagen | `300` |
| `JOB_TIMEOUT` | Timeout para jobs (segundos) | `3600` |
| `MAX_UPLOAD_SIZE` | Tamaño máximo de archivo (bytes) | `104857600` (100MB) |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

### Escalar Workers

Para procesar múltiples PDFs simultáneamente, ajustar en `docker-compose.yml`:

```yaml
worker:
  deploy:
    replicas: 4  # Número de workers
```

Luego:

```bash
docker-compose up -d --scale worker=4
```

## Comandos Útiles (Makefile)

```bash
make help           # Muestra ayuda
make build          # Construye imágenes
make up             # Inicia servicios
make down           # Detiene servicios
make restart        # Reinicia servicios
make logs           # Ver logs de todos los servicios
make logs-api       # Ver logs del API
make logs-worker    # Ver logs del worker
make shell-api      # Shell en contenedor API
make shell-db       # Shell en PostgreSQL
make clean          # Limpia todo (contenedores, volúmenes)
make clean-storage  # Limpia archivos de storage
make status         # Estado de servicios
```

## Troubleshooting

### Error: "No se puede conectar a la base de datos"

```bash
# Verificar estado de PostgreSQL
docker-compose ps db

# Ver logs
docker-compose logs db

# Reiniciar servicio
docker-compose restart db
```

### Error: "Worker no procesa jobs"

```bash
# Verificar estado de Redis
docker-compose ps redis

# Ver logs del worker
docker-compose logs worker

# Reiniciar worker
docker-compose restart worker
```

### Error: "OCR no funciona"

Verificar que Tesseract esté instalado en el contenedor:

```bash
docker-compose exec backend tesseract --version
```

### Limpiar todo y empezar de nuevo

```bash
make clean
make build
make up
```

## Desarrollo

### Ejecutar sin Docker

```bash
# Instalar dependencias
cd backend
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql://pdfuser:pdfpass@localhost:5432/pdfdb"
export REDIS_URL="redis://localhost:6379/0"
# ... otras variables

# Iniciar API
python -m uvicorn app.main:app --reload

# Iniciar worker (en otra terminal)
python -m app.workers.worker
```

### Tests

```bash
# Implementar según necesidad
pytest tests/
```

## Seguridad

- ✅ Usuario no privilegiado en contenedores
- ✅ Sanitización de nombres de archivo
- ✅ Validación de tipos de archivo
- ✅ Límite de tamaño de archivo
- ✅ Sin exposición de credenciales
- ⚠️ En producción: Configurar CORS adecuadamente
- ⚠️ En producción: Usar HTTPS
- ⚠️ En producción: Cambiar contraseñas por defecto

## Rendimiento

### Tiempos Estimados

- PDF de 10 páginas: ~5-10 segundos
- PDF de 50 páginas: ~20-40 segundos
- PDF de 100 páginas: ~45-90 segundos

*Depende del hardware, DPI configurado y complejidad del documento*

### Optimización

1. **Reducir DPI**: Cambiar `PDF_DPI` a 200 (más rápido, menos preciso)
2. **Escalar workers**: Aumentar número de workers
3. **Memoria**: Asignar más RAM a Docker
4. **Disco SSD**: Usar almacenamiento SSD para mejor I/O

## Licencia

Ver archivo [LICENSE](LICENSE)

## Soporte

Para reportar problemas o sugerencias, crear un issue en el repositorio.

## Roadmap

- [ ] Tests unitarios y de integración
- [ ] Soporte para más idiomas OCR
- [ ] API de webhooks para notificaciones
- [ ] Frontend web
- [ ] Exportación a ZIP
- [ ] Integración con firma digital
- [ ] Métricas y monitoreo (Prometheus/Grafana)
