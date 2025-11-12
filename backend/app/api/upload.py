"""
Endpoint de subida de archivos
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
import shutil
from pathlib import Path
from app.config import settings
from app.db.database import get_db
from app.db.models import Job, JobStatus
from app.core.utils import generate_job_id, sanitize_filename, ensure_dir
from app.workers.worker import process_pdf_job

router = APIRouter()


def get_redis_conn():
    """Obtiene conexión a Redis"""
    return Redis.from_url(settings.REDIS_URL)


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Sube un archivo PDF para procesamiento

    Args:
        file: Archivo PDF a procesar
        db: Sesión de base de datos

    Returns:
        Información del job creado
    """
    # Validar tipo de archivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF"
        )

    # Validar tamaño (se hace en memoria)
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo demasiado grande. Máximo: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )

    # Generar ID de job
    job_id = generate_job_id()

    # Sanitizar nombre de archivo
    safe_filename = sanitize_filename(file.filename)

    # Guardar archivo en storage/input
    input_dir = ensure_dir(settings.STORAGE_INPUT)
    file_path = input_dir / f"{job_id}_{safe_filename}"

    try:
        with open(file_path, 'wb') as f:
            f.write(content)

        # Crear registro en base de datos
        job = Job(
            job_id=job_id,
            filename=safe_filename,
            status=JobStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Encolar trabajo en RQ
        redis_conn = get_redis_conn()
        queue = Queue('default', connection=redis_conn)

        rq_job = queue.enqueue(
            process_pdf_job,
            job_id=job_id,
            filename=safe_filename,
            file_path=str(file_path),
            job_timeout=settings.JOB_TIMEOUT
        )

        return {
            "job_id": job_id,
            "filename": safe_filename,
            "status": job.status.value,
            "message": "Archivo subido exitosamente. Procesamiento iniciado.",
            "rq_job_id": rq_job.id
        }

    except Exception as e:
        # Limpiar archivo si hay error
        if file_path.exists():
            file_path.unlink()

        # Eliminar job de DB si se creó
        if 'job' in locals():
            db.delete(job)
            db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar archivo: {str(e)}"
        )
