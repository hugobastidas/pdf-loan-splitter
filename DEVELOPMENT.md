# Guía de Desarrollo - PDF Classifier

Esta guía está diseñada para desarrolladores que quieren contribuir o extender el proyecto.

## Configuración del Entorno de Desarrollo

### Opción 1: Desarrollo con Docker (Recomendado)

```bash
# Construir imágenes
make build

# Iniciar servicios
make dev

# Ver logs en tiempo real
make logs
```

### Opción 2: Desarrollo Local (Sin Docker)

**Requisitos:**
- Python 3.11
- PostgreSQL 16
- Redis 7
- Tesseract OCR con idioma español
- poppler-utils
- libzbar0

**Instalación en Ubuntu/Debian:**

```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libzbar0 \
    poppler-utils \
    postgresql-16 \
    redis-server

# Instalar Pipenv
pip install --user pipenv

# Instalar dependencias Python con Pipenv
cd backend
pipenv install --dev

# Activar entorno virtual
pipenv shell
```

**Configurar servicios:**

```bash
# PostgreSQL
sudo -u postgres psql
CREATE DATABASE pdfdb;
CREATE USER pdfuser WITH PASSWORD 'pdfpass';
GRANT ALL PRIVILEGES ON DATABASE pdfdb TO pdfuser;
\q

# Redis (ya debería estar corriendo)
sudo systemctl start redis-server
```

**Configurar variables de entorno:**

```bash
export DATABASE_URL="postgresql://pdfuser:pdfpass@localhost:5432/pdfdb"
export REDIS_URL="redis://localhost:6379/0"
export STORAGE_ROOT="$(pwd)/../storage"
export TIMEZONE="America/Guayaquil"
export LOG_LEVEL="DEBUG"
```

**Iniciar servicios:**

```bash
# Terminal 1: API
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Worker
cd backend
python -m app.workers.worker
```

## Estructura del Código

### Módulos Principales

#### 1. `app/config.py`
Configuración centralizada usando Pydantic Settings.

```python
from app.config import settings

# Acceder a configuración
print(settings.DATABASE_URL)
print(settings.STORAGE_ROOT)
```

#### 2. `app/db/models.py`
Modelos de base de datos con SQLAlchemy.

**Modelos:**
- `Job`: Información de trabajos de procesamiento
- `Document`: Documentos procesados
- `ProcessingLog`: Logs de procesamiento

#### 3. `app/core/pdf_processor.py`
Procesador principal de PDFs.

**Métodos principales:**
- `convert_pdf_to_images()`: Convierte PDF a imágenes
- `is_blank_page()`: Detecta páginas en blanco
- `detect_barcode()`: Detecta códigos de barras
- `extract_text_ocr()`: Extrae texto con OCR
- `classify_document()`: Clasifica tipo de documento
- `analyze_pages()`: Analiza todas las páginas
- `split_pdf_by_separators()`: Divide el PDF
- `process_pdf()`: Método principal de procesamiento

#### 4. `app/workers/worker.py`
Worker RQ para procesamiento asíncrono.

**Funciones:**
- `process_pdf_job()`: Procesa un PDF en background
- `log_processing()`: Registra logs de procesamiento
- `run_worker()`: Ejecuta el worker

#### 5. `app/api/`
Endpoints de la API REST.

- `upload.py`: Upload de archivos
- `jobs.py`: Consulta de jobs
- `documents.py`: Consulta de documentos

## Agregar Nuevas Funcionalidades

### Agregar un Nuevo Tipo de Documento

1. **Actualizar enum en `models.py`:**

```python
class DocumentType(str, enum.Enum):
    # ... tipos existentes
    NUEVO_TIPO = "nuevo_tipo"
```

2. **Actualizar clasificador en `pdf_processor.py`:**

```python
def classify_document(self, barcode_value: Optional[str] = None,
                     ocr_text: Optional[str] = None) -> DocumentType:
    # ...
    if barcode_value:
        barcode_upper = barcode_value.upper()

        # Agregar lógica para nuevo tipo
        if 'PALABRA_CLAVE' in barcode_upper:
            return DocumentType.NUEVO_TIPO

    # Agregar keywords OCR
    keywords = {
        # ...
        DocumentType.NUEVO_TIPO: ['KEYWORD1', 'KEYWORD2'],
    }
```

### Agregar un Nuevo Endpoint

1. **Crear archivo en `app/api/`:**

```python
# app/api/my_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    return {"message": "Hello from my endpoint"}
```

2. **Registrar en `main.py`:**

```python
from app.api import upload, jobs, documents, my_endpoint

# ...

app.include_router(my_endpoint.router, prefix="/api", tags=["MyEndpoint"])
```

### Agregar Validación Personalizada

Crear validador en `app/core/validators.py`:

```python
def validate_pdf_content(pdf_path: Path) -> bool:
    """Valida contenido del PDF"""
    try:
        # Tu lógica de validación
        return True
    except Exception:
        return False
```

## Testing

### Tests Unitarios

Crear tests en directorio `backend/tests/`:

```python
# tests/test_pdf_processor.py
import pytest
from pathlib import Path
from app.core.pdf_processor import PDFProcessor

def test_blank_page_detection():
    processor = PDFProcessor()
    # Crear imagen de prueba en blanco
    # ...
    assert processor.is_blank_page(blank_image) == True

def test_barcode_detection():
    processor = PDFProcessor()
    # Crear imagen de prueba con código de barras
    # ...
    result = processor.detect_barcode(barcode_image)
    assert result is not None
    assert result['value'] == 'EXPECTED_VALUE'
```

**Ejecutar tests:**

```bash
pytest tests/ -v
pytest tests/test_pdf_processor.py -v
pytest tests/ --cov=app --cov-report=html
```

### Tests de Integración

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_pdf():
    with open("test_files/sample.pdf", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("sample.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    assert "job_id" in response.json()
```

## Debugging

### Logs

**Aumentar nivel de logging:**

```python
# En config.py o .env
LOG_LEVEL=DEBUG
```

**Ver logs del procesamiento:**

```bash
# Docker
docker-compose logs -f worker

# Local
# Los logs aparecerán en la terminal donde ejecutaste el worker
```

### Debugging con VSCode

Crear `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "DATABASE_URL": "postgresql://pdfuser:pdfpass@localhost:5432/pdfdb",
        "REDIS_URL": "redis://localhost:6379/0"
      }
    },
    {
      "name": "Worker",
      "type": "python",
      "request": "launch",
      "module": "app.workers.worker",
      "justMyCode": false,
      "env": {
        "DATABASE_URL": "postgresql://pdfuser:pdfpass@localhost:5432/pdfdb",
        "REDIS_URL": "redis://localhost:6379/0"
      }
    }
  ]
}
```

### Debugging del Procesamiento de PDF

Agregar logs detallados en `pdf_processor.py`:

```python
import logging
logger = logging.getLogger(__name__)

def process_pdf(self, pdf_path: Path, output_dir: Path) -> Dict:
    logger.debug(f"Procesando PDF: {pdf_path}")
    logger.debug(f"Output dir: {output_dir}")

    # ... procesamiento

    logger.debug(f"Páginas analizadas: {len(pages_info)}")
    for i, page_info in enumerate(pages_info):
        logger.debug(f"Página {i+1}: {page_info}")
```

## Optimización

### Rendimiento del OCR

```python
# Reducir DPI para procesamiento más rápido
PDF_DPI=200  # En lugar de 300

# Usar OCR solo cuando sea necesario
# En pdf_processor.py, solo hacer OCR si no hay barcode
```

### Procesamiento Paralelo

```python
# Procesar múltiples páginas en paralelo
from concurrent.futures import ThreadPoolExecutor

def analyze_pages(self, images: List[Image.Image]) -> List[Dict]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(self._analyze_single_page, images))
    return results

def _analyze_single_page(self, image: Image.Image) -> Dict:
    # Lógica de análisis
    pass
```

### Caché de Resultados

Agregar caché Redis para resultados frecuentes:

```python
import json
from redis import Redis

def get_cached_result(key: str) -> Optional[Dict]:
    redis = Redis.from_url(settings.REDIS_URL)
    result = redis.get(key)
    return json.loads(result) if result else None

def cache_result(key: str, result: Dict, ttl: int = 3600):
    redis = Redis.from_url(settings.REDIS_URL)
    redis.setex(key, ttl, json.dumps(result))
```

## Buenas Prácticas

### Code Style

Usar Black para formateo automático:

```bash
pip install black
black backend/app/
```

Usar Ruff para linting:

```bash
pip install ruff
ruff check backend/app/
```

### Type Hints

Siempre usar type hints:

```python
from typing import List, Optional, Dict

def process_data(
    items: List[str],
    options: Optional[Dict] = None
) -> Dict[str, int]:
    # ...
    return result
```

### Manejo de Errores

Siempre manejar excepciones específicas:

```python
try:
    result = process_pdf(path)
except FileNotFoundError:
    logger.error(f"Archivo no encontrado: {path}")
    raise
except Exception as e:
    logger.error(f"Error inesperado: {e}", exc_info=True)
    raise
```

### Logging

Usar niveles apropiados:

```python
logger.debug("Información detallada para debugging")
logger.info("Información general del flujo")
logger.warning("Situación anómala pero manejable")
logger.error("Error que requiere atención")
logger.critical("Error crítico que detiene la aplicación")
```

## Contribuir

1. Fork el repositorio
2. Crear rama de feature: `git checkout -b feature/mi-feature`
3. Commit cambios: `git commit -am 'Agregar mi feature'`
4. Push a la rama: `git push origin feature/mi-feature`
5. Crear Pull Request

### Checklist antes de PR

- [ ] Código sigue las convenciones de estilo
- [ ] Tests pasan correctamente
- [ ] Documentación actualizada
- [ ] Sin warnings de linting
- [ ] Type hints agregados
- [ ] Logs apropiados agregados

## Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [RQ Docs](https://python-rq.org/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyZbar Docs](https://github.com/NaturalHistoryMuseum/pyzbar)
