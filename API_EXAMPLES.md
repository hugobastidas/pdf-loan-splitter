# Ejemplos de Uso de la API

Este documento contiene ejemplos prácticos de cómo usar la API PDF Classifier.

## Configuración Inicial

```bash
# URL base de la API
API_URL="http://localhost:8000"

# O en producción
API_URL="https://api.pdfclassifier.com"
```

## 1. Health Check

### cURL

```bash
curl -X GET "${API_URL}/health"
```

### Python

```python
import requests

response = requests.get(f"{API_URL}/health")
print(response.json())
```

### JavaScript

```javascript
fetch(`${API_URL}/health`)
  .then(response => response.json())
  .then(data => console.log(data));
```

**Respuesta:**
```json
{
  "status": "healthy",
  "storage_input": "/app/storage/input",
  "storage_output": "/app/storage/output"
}
```

## 2. Subir PDF para Procesamiento

### cURL

```bash
curl -X POST "${API_URL}/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/documento.pdf"
```

### Python

```python
import requests

# Subir archivo
with open('documento.pdf', 'rb') as f:
    files = {'file': ('documento.pdf', f, 'application/pdf')}
    response = requests.post(f"{API_URL}/api/upload", files=files)

result = response.json()
job_id = result['job_id']
print(f"Job creado: {job_id}")
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('documento.pdf'));

axios.post(`${API_URL}/api/upload`, form, {
  headers: form.getHeaders()
})
.then(response => {
  console.log('Job ID:', response.data.job_id);
})
.catch(error => console.error(error));
```

### JavaScript (Browser)

```javascript
const fileInput = document.getElementById('pdfFile');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);

fetch(`${API_URL}/api/upload`, {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Job ID:', data.job_id);
});
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

## 3. Consultar Estado de un Job

### cURL

```bash
JOB_ID="job_abc123def456"
curl -X GET "${API_URL}/api/jobs/${JOB_ID}"
```

### Python

```python
import requests
import time

job_id = "job_abc123def456"

# Polling hasta que se complete
while True:
    response = requests.get(f"{API_URL}/api/jobs/{job_id}")
    job = response.json()

    status = job['status']
    print(f"Estado: {status}")

    if status in ['completed', 'failed']:
        break

    time.sleep(2)  # Esperar 2 segundos

print(f"Job finalizado: {job}")
```

### JavaScript

```javascript
const checkJobStatus = async (jobId) => {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`);
  const job = await response.json();
  return job;
};

// Polling
const pollJob = async (jobId) => {
  while (true) {
    const job = await checkJobStatus(jobId);
    console.log('Estado:', job.status);

    if (job.status === 'completed' || job.status === 'failed') {
      return job;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }
};

// Uso
pollJob('job_abc123def456')
  .then(job => console.log('Job finalizado:', job));
```

**Respuesta (Pending):**
```json
{
  "job_id": "job_abc123def456",
  "filename": "documento.pdf",
  "status": "pending",
  "total_pages": null,
  "processed_pages": 0,
  "documents_created": 0,
  "error_message": null,
  "processing_time": null,
  "created_at": "2024-01-15T10:30:00",
  "started_at": null,
  "completed_at": null
}
```

**Respuesta (Completed):**
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

## 4. Listar Todos los Jobs

### cURL

```bash
# Todos los jobs (últimos 50)
curl -X GET "${API_URL}/api/jobs"

# Con filtros
curl -X GET "${API_URL}/api/jobs?status=completed&limit=10"

# Paginación
curl -X GET "${API_URL}/api/jobs?limit=20&offset=20"
```

### Python

```python
# Listar todos los jobs completados
params = {
    'status': 'completed',
    'limit': 50
}
response = requests.get(f"{API_URL}/api/jobs", params=params)
jobs = response.json()

for job in jobs:
    print(f"{job['job_id']}: {job['filename']} - {job['status']}")
```

## 5. Ver Logs de un Job

### cURL

```bash
JOB_ID="job_abc123def456"
curl -X GET "${API_URL}/api/jobs/${JOB_ID}/logs"
```

### Python

```python
job_id = "job_abc123def456"
response = requests.get(f"{API_URL}/api/jobs/{job_id}/logs")
logs = response.json()

for log in logs:
    print(f"[{log['level']}] {log['timestamp']}: {log['message']}")
```

**Respuesta:**
```json
[
  {
    "level": "INFO",
    "message": "Iniciando procesamiento de documento.pdf",
    "timestamp": "2024-01-15T10:30:05"
  },
  {
    "level": "INFO",
    "message": "Procesamiento completado. 5 documentos creados en 12.34s",
    "timestamp": "2024-01-15T10:30:17"
  }
]
```

## 6. Listar Documentos Procesados

### cURL

```bash
# Todos los documentos
curl -X GET "${API_URL}/api/documents"

# Por job
curl -X GET "${API_URL}/api/documents?job_id=job_abc123def456"

# Por tipo
curl -X GET "${API_URL}/api/documents?document_type=cedula"

# Combinado
curl -X GET "${API_URL}/api/documents?job_id=job_abc123def456&limit=10"
```

### Python

```python
# Listar documentos de un job
params = {
    'job_id': 'job_abc123def456'
}
response = requests.get(f"{API_URL}/api/documents", params=params)
documents = response.json()

for doc in documents:
    print(f"{doc['filename']} - {doc['document_type']}")
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "job_id": "job_abc123def456",
    "document_type": "cedula",
    "barcode_value": "CEDULA_001",
    "barcode_type": "CODE128",
    "filename": "documento_doc_1.pdf",
    "page_start": 1,
    "page_end": 5,
    "total_pages": 5,
    "has_blank_pages": 1,
    "created_at": "2024-01-15T10:30:17"
  },
  {
    "id": 2,
    "job_id": "job_abc123def456",
    "document_type": "certificado",
    "barcode_value": "CERT_002",
    "barcode_type": "CODE128",
    "filename": "documento_doc_2.pdf",
    "page_start": 6,
    "page_end": 10,
    "total_pages": 4,
    "has_blank_pages": 0,
    "created_at": "2024-01-15T10:30:17"
  }
]
```

## 7. Ver Detalle de un Documento

### cURL

```bash
DOCUMENT_ID=1
curl -X GET "${API_URL}/api/documents/${DOCUMENT_ID}"
```

### Python

```python
document_id = 1
response = requests.get(f"{API_URL}/api/documents/{document_id}")
document = response.json()

print(f"Tipo: {document['document_type']}")
print(f"Páginas: {document['total_pages']}")
print(f"Código: {document['barcode_value']}")
print(f"OCR: {document['ocr_text'][:100]}...")  # Primeros 100 caracteres
```

**Respuesta:**
```json
{
  "id": 1,
  "job_id": "job_abc123def456",
  "document_type": "cedula",
  "barcode_value": "CEDULA_001",
  "barcode_type": "CODE128",
  "filename": "documento_doc_1.pdf",
  "file_path": "/app/storage/output/job_abc123def456/documento_doc_1.pdf",
  "page_start": 1,
  "page_end": 5,
  "total_pages": 5,
  "has_blank_pages": 1,
  "ocr_text": "REPÚBLICA DEL ECUADOR...",
  "created_at": "2024-01-15T10:30:17"
}
```

## 8. Descargar Documento Procesado

### cURL

```bash
DOCUMENT_ID=1
curl -X GET "${API_URL}/api/documents/${DOCUMENT_ID}/download" \
  -o documento_descargado.pdf
```

### Python

```python
document_id = 1
response = requests.get(f"{API_URL}/api/documents/{document_id}/download")

# Guardar archivo
with open('documento_descargado.pdf', 'wb') as f:
    f.write(response.content)

print("Documento descargado exitosamente")
```

### JavaScript (Browser)

```javascript
const downloadDocument = async (documentId) => {
  const response = await fetch(`${API_URL}/api/documents/${documentId}/download`);
  const blob = await response.blob();

  // Crear link de descarga
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'documento.pdf';
  document.body.appendChild(a);
  a.click();
  a.remove();
};

downloadDocument(1);
```

## 9. Flujo Completo de Procesamiento

### Python

```python
import requests
import time

API_URL = "http://localhost:8000"

# 1. Subir PDF
print("1. Subiendo PDF...")
with open('mi_documento.pdf', 'rb') as f:
    files = {'file': ('mi_documento.pdf', f, 'application/pdf')}
    response = requests.post(f"{API_URL}/api/upload", files=files)

result = response.json()
job_id = result['job_id']
print(f"   Job creado: {job_id}")

# 2. Esperar a que se complete
print("2. Esperando procesamiento...")
while True:
    response = requests.get(f"{API_URL}/api/jobs/{job_id}")
    job = response.json()
    status = job['status']

    if status == 'completed':
        print(f"   ✓ Completado en {job['processing_time']:.2f}s")
        print(f"   Documentos creados: {job['documents_created']}")
        break
    elif status == 'failed':
        print(f"   ✗ Error: {job['error_message']}")
        break
    else:
        print(f"   Estado: {status}...")
        time.sleep(2)

# 3. Obtener documentos procesados
if job['status'] == 'completed':
    print("3. Obteniendo documentos...")
    response = requests.get(f"{API_URL}/api/documents", params={'job_id': job_id})
    documents = response.json()

    # 4. Descargar cada documento
    print("4. Descargando documentos...")
    for doc in documents:
        print(f"   - {doc['filename']} ({doc['document_type']})")

        response = requests.get(f"{API_URL}/api/documents/{doc['id']}/download")
        with open(doc['filename'], 'wb') as f:
            f.write(response.content)

    print("✓ Proceso completado!")
```

### Bash Script

```bash
#!/bin/bash

API_URL="http://localhost:8000"
PDF_FILE="mi_documento.pdf"

# 1. Subir PDF
echo "1. Subiendo PDF..."
RESPONSE=$(curl -s -X POST "${API_URL}/api/upload" \
  -F "file=@${PDF_FILE}")

JOB_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "   Job creado: $JOB_ID"

# 2. Esperar completado
echo "2. Esperando procesamiento..."
while true; do
    STATUS=$(curl -s "${API_URL}/api/jobs/${JOB_ID}" | \
      python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

    if [ "$STATUS" = "completed" ]; then
        echo "   ✓ Completado"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "   ✗ Error"
        exit 1
    fi

    echo "   Estado: $STATUS..."
    sleep 2
done

# 3. Listar documentos
echo "3. Listando documentos..."
curl -s "${API_URL}/api/documents?job_id=${JOB_ID}" | python3 -m json.tool

echo "✓ Proceso completado!"
```

## 10. Manejo de Errores

### Archivo muy grande

```python
try:
    with open('archivo_grande.pdf', 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{API_URL}/api/upload", files=files)
        response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("Error: Archivo demasiado grande")
    else:
        print(f"Error HTTP: {e}")
```

### Tipo de archivo incorrecto

```python
try:
    with open('documento.txt', 'rb') as f:
        files = {'file': ('documento.txt', f, 'text/plain')}
        response = requests.post(f"{API_URL}/api/upload", files=files)
        response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error = e.response.json()
    print(f"Error: {error['detail']}")  # "Solo se permiten archivos PDF"
```

### Job no encontrado

```python
job_id = "job_inexistente"
response = requests.get(f"{API_URL}/api/jobs/{job_id}")

if response.status_code == 404:
    print(f"Job {job_id} no encontrado")
```

## Tipos de Documentos Soportados

| Código | Descripción |
|--------|-------------|
| `cedula` | Cédula de identidad |
| `certificado` | Certificados generales |
| `papeleta_votacion` | Papeleta de votación |
| `mecanizado` | Planilla mecanizada IESS |
| `planilla_servicios` | Planillas de servicios básicos |
| `certificado_cuenta` | Certificado bancario |
| `unknown` | No clasificado |

## Estados de Jobs

| Estado | Descripción |
|--------|-------------|
| `pending` | En cola, esperando procesamiento |
| `processing` | Siendo procesado actualmente |
| `completed` | Completado exitosamente |
| `failed` | Falló durante el procesamiento |

## Límites y Restricciones

- **Tamaño máximo de archivo**: 100 MB (configurable)
- **Tipos de archivo permitidos**: Solo PDF
- **Timeout de procesamiento**: 3600 segundos (1 hora)
- **Rate limiting**: No implementado (próximamente)
