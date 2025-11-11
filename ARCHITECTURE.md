# Arquitectura Técnica - PDF Classifier

Este documento describe la arquitectura técnica del sistema PDF Classifier.

## Visión General

PDF Classifier es un sistema backend diseñado para procesar, clasificar y dividir documentos PDF basándose en páginas separadoras con códigos de barras. El sistema utiliza una arquitectura de microservicios con procesamiento asíncrono.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Cliente (API REST)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/JSON
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Upload     │  │    Jobs      │  │  Documents   │     │
│  │   Endpoint   │  │   Endpoint   │  │   Endpoint   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────┬─────────────────┬───────────────────┬──────────────┘
        │                 │                   │
        │ Enqueue         │ Query             │ Query
        ▼                 ▼                   ▼
┌──────────────┐   ┌────────────────────────────┐
│    Redis     │   │       PostgreSQL           │
│  (Job Queue) │   │    (Metadata & Jobs)       │
└──────┬───────┘   └────────────────────────────┘
       │
       │ Dequeue
       ▼
┌─────────────────────────────────────────────────────────────┐
│                       RQ Worker(s)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PDF Processor                          │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │   │
│  │  │ PDF to IMG │→│  Barcode   │→│  OCR (Tesseract)│ │   │
│  │  │            │ │  Detection │ │                 │ │   │
│  │  │ (pdf2image)│ │  (pyzbar)  │ │                 │ │   │
│  │  └────────────┘ └────────────┘ └────────────────┘  │   │
│  │         │              │                │           │   │
│  │         └──────────────┴────────────────┘           │   │
│  │                        │                            │   │
│  │                        ▼                            │   │
│  │         ┌────────────────────────────┐              │   │
│  │         │   Blank Page Detection     │              │   │
│  │         │   Document Classification  │              │   │
│  │         │   PDF Splitting (PyPDF)    │              │   │
│  │         └────────────────────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │  File System       │
                 │  storage/input/    │
                 │  storage/output/   │
                 └────────────────────┘
```

## Componentes Principales

### 1. FastAPI Application (API Layer)

**Responsabilidades:**
- Exponer API REST para clientes
- Validar requests
- Autenticación (futura)
- Encolar trabajos de procesamiento
- Consultar estado y resultados

**Tecnologías:**
- FastAPI: Framework web asíncrono
- Pydantic: Validación de datos
- SQLAlchemy: ORM para PostgreSQL

**Endpoints:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/upload` | Subir PDF para procesamiento |
| GET | `/api/jobs` | Listar jobs |
| GET | `/api/jobs/{job_id}` | Consultar job específico |
| GET | `/api/jobs/{job_id}/logs` | Ver logs de un job |
| GET | `/api/documents` | Listar documentos procesados |
| GET | `/api/documents/{id}` | Ver detalle de documento |
| GET | `/api/documents/{id}/download` | Descargar documento |

### 2. Redis (Message Queue)

**Responsabilidades:**
- Cola de trabajos de procesamiento
- Gestión de estado de jobs
- Cache (futura funcionalidad)

**Configuración:**
- Persistencia: AOF (Append Only File)
- Puerto: 6379
- Queue: `default`

### 3. PostgreSQL (Database)

**Responsabilidades:**
- Almacenar metadatos de jobs
- Almacenar información de documentos procesados
- Logs de procesamiento
- Auditoría

**Esquema:**

```sql
-- Jobs
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_pages INTEGER,
    processed_pages INTEGER DEFAULT 0,
    documents_created INTEGER DEFAULT 0,
    error_message TEXT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Documents
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    document_type VARCHAR(50) NOT NULL,
    barcode_value VARCHAR(255),
    barcode_type VARCHAR(50),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    total_pages INTEGER NOT NULL,
    has_blank_pages INTEGER DEFAULT 0,
    ocr_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Processing Logs
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata TEXT
);
```

### 4. RQ Worker (Processing Layer)

**Responsabilidades:**
- Procesar PDFs de forma asíncrona
- Ejecutar pipeline de procesamiento
- Actualizar estado en DB
- Registrar logs

**Pipeline de Procesamiento:**

```
1. Recibir Job
   ↓
2. Convertir PDF a Imágenes (pdf2image)
   ↓
3. Analizar cada página:
   - Detectar si es blanca (OpenCV)
   - Detectar código de barras (pyzbar)
   - Extraer texto OCR si no hay barcode (Tesseract)
   ↓
4. Identificar páginas separadoras (con barcode)
   ↓
5. Dividir PDF por separadores (PyPDF)
   ↓
6. Clasificar cada documento (basado en barcode/OCR)
   ↓
7. Guardar documentos en storage/output
   ↓
8. Registrar metadatos en DB
   ↓
9. Actualizar estado del job
```

**Configuración:**
- Workers concurrentes: 2 (configurable)
- Timeout por job: 3600s (1 hora)
- Reintentos: 0 (sin reintentos automáticos)

### 5. PDF Processor (Core Logic)

**Módulos:**

#### a) Conversión PDF → Imágenes
```python
def convert_pdf_to_images(pdf_path: Path) -> List[Image.Image]:
    # Usa pdf2image (wrapper de poppler)
    # DPI configurable (default: 300)
```

#### b) Detección de Páginas en Blanco
```python
def is_blank_page(image: Image.Image) -> bool:
    # Convierte a escala de grises
    # Calcula ratio de píxeles blancos
    # Umbral configurable (default: 0.98)
```

#### c) Detección de Códigos de Barras
```python
def detect_barcode(image: Image.Image) -> Optional[Dict]:
    # Usa pyzbar (zbar)
    # Soporta múltiples formatos: CODE128, CODE39, QR, etc.
    # Devuelve: {value, type}
```

#### d) OCR
```python
def extract_text_ocr(image: Image.Image) -> str:
    # Usa Tesseract OCR
    # Idioma: español (configurable)
    # PSM: 3 (Automatic page segmentation)
```

#### e) Clasificación de Documentos
```python
def classify_document(barcode_value, ocr_text) -> DocumentType:
    # Prioridad 1: Clasificación por barcode
    # Prioridad 2: Clasificación por keywords OCR
    # Default: UNKNOWN
```

#### f) División de PDF
```python
def split_pdf_by_separators(pdf_path, pages_info, output_dir):
    # Identifica índices de separadores
    # Extrae rangos de páginas
    # Elimina páginas en blanco
    # Guarda PDFs individuales
```

## Flujo de Datos

### 1. Upload de Archivo

```
Cliente → POST /api/upload
    ↓
FastAPI valida archivo
    ↓
Guarda en storage/input/
    ↓
Crea Job en PostgreSQL (status: PENDING)
    ↓
Encola en Redis
    ↓
Responde al cliente con job_id
```

### 2. Procesamiento Asíncrono

```
Worker toma job de Redis
    ↓
Actualiza status → PROCESSING
    ↓
Ejecuta PDF Processor
    ↓
Por cada página separadora:
    - Crea subdocumento
    - Guarda en storage/output/{job_id}/
    - Registra en tabla documents
    ↓
Actualiza status → COMPLETED (o FAILED)
    ↓
Registra tiempo de procesamiento
```

### 3. Consulta de Resultados

```
Cliente → GET /api/jobs/{job_id}
    ↓
FastAPI consulta PostgreSQL
    ↓
Devuelve estado y metadatos
    ↓
Cliente → GET /api/documents?job_id={job_id}
    ↓
FastAPI consulta PostgreSQL
    ↓
Devuelve lista de documentos
    ↓
Cliente → GET /api/documents/{id}/download
    ↓
FastAPI lee archivo de storage/output/
    ↓
Devuelve PDF
```

## Modelo de Datos

### Job
```python
{
    "job_id": "job_abc123",
    "filename": "documento.pdf",
    "status": "completed",
    "total_pages": 25,
    "processed_pages": 25,
    "documents_created": 5,
    "processing_time": 12.34,
    "created_at": "2024-01-15T10:30:00",
    "completed_at": "2024-01-15T10:30:12"
}
```

### Document
```python
{
    "id": 1,
    "job_id": "job_abc123",
    "document_type": "cedula",
    "barcode_value": "CEDULA_001",
    "barcode_type": "CODE128",
    "filename": "documento_doc_1.pdf",
    "page_start": 1,
    "page_end": 5,
    "total_pages": 5,
    "has_blank_pages": 1
}
```

## Decisiones de Diseño

### ¿Por qué RQ en lugar de Celery?

**RQ (Redis Queue):**
- ✅ Más simple y ligero
- ✅ Menor overhead
- ✅ Suficiente para este caso de uso
- ❌ Menos features que Celery

**Celery:**
- ✅ Más features (retries, schedules, etc.)
- ✅ Soporta múltiples brokers
- ❌ Mayor complejidad
- ❌ Overhead innecesario para este proyecto

### ¿Por qué PyMuPDF + pdf2image + PyPDF?

- **PyMuPDF (fitz)**: Lectura rápida de PDFs
- **pdf2image**: Conversión de PDF a imágenes (usa poppler)
- **PyPDF**: Manipulación de PDFs (división, merge)

Cada librería tiene su especialidad y juntas cubren todas las necesidades.

### ¿Por qué PostgreSQL en lugar de SQLite?

- ✅ Mejor concurrencia
- ✅ Preparado para escalabilidad
- ✅ Tipos de datos más ricos
- ✅ Transacciones ACID completas

## Seguridad

### Implementadas

1. **Validación de archivos**: Solo PDFs permitidos
2. **Límite de tamaño**: 100MB por defecto
3. **Sanitización de nombres**: Elimina caracteres peligrosos
4. **Usuario no privilegiado**: Contenedores corren como `pdfuser`
5. **Aislamiento**: Red Docker privada

### Futuras

1. **Autenticación**: JWT tokens
2. **Rate limiting**: Límite de requests por IP
3. **Virus scanning**: ClamAV integrado
4. **Cifrado**: Archivos sensibles cifrados en disco
5. **Auditoría**: Logs completos de accesos

## Escalabilidad

### Horizontal Scaling

```bash
# Escalar workers
docker-compose up -d --scale worker=10
```

### Vertical Scaling

- Aumentar recursos de contenedores
- Optimizar DPI de procesamiento
- Cache de resultados

### Optimizaciones Futuras

1. **Procesamiento paralelo de páginas**: ThreadPoolExecutor
2. **Cache Redis**: Resultados de OCR frecuentes
3. **CDN**: Para descarga de documentos
4. **Object Storage**: S3-compatible para archivos
5. **Load Balancer**: nginx para múltiples instancias API

## Monitoreo (Futuro)

### Métricas Propuestas

- Jobs procesados por minuto
- Tiempo promedio de procesamiento
- Tasa de errores
- Uso de disco en storage/
- Queue size en Redis
- Conexiones activas a PostgreSQL

### Stack Propuesto

- **Prometheus**: Recolección de métricas
- **Grafana**: Visualización
- **Loki**: Logs centralizados
- **AlertManager**: Alertas

## Limitaciones Actuales

1. **Sin autenticación**: Cualquiera puede usar la API
2. **Sin rate limiting**: Posible abuso
3. **Sin reintentos**: Jobs fallidos no se reintentan
4. **Sin limpieza automática**: Archivos viejos se acumulan
5. **Sin validación avanzada**: No detecta PDFs corruptos antes de procesar

## Roadmap Técnico

### Fase 1 (Actual)
- [x] API REST funcional
- [x] Procesamiento asíncrono
- [x] OCR en español
- [x] Detección de códigos de barras
- [x] División de PDFs
- [x] Clasificación básica

### Fase 2 (Corto plazo)
- [ ] Tests unitarios y de integración
- [ ] Autenticación JWT
- [ ] Rate limiting
- [ ] Validación avanzada de PDFs

### Fase 3 (Mediano plazo)
- [ ] Frontend web
- [ ] Webhooks para notificaciones
- [ ] Exportación masiva (ZIP)
- [ ] Métricas y monitoreo

### Fase 4 (Largo plazo)
- [ ] Integración con firma digital
- [ ] Machine Learning para clasificación
- [ ] Procesamiento de imágenes (no solo PDF)
- [ ] API GraphQL
