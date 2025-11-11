"""
Endpoint para consulta de jobs
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.database import get_db
from app.db.models import Job, JobStatus, ProcessingLog

router = APIRouter()


class JobResponse(BaseModel):
    """Respuesta de información de job"""
    job_id: str
    filename: str
    status: str
    total_pages: Optional[int]
    processed_pages: int
    documents_created: int
    error_message: Optional[str]
    processing_time: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    """Respuesta de log de procesamiento"""
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Obtiene información de un job específico

    Args:
        job_id: ID del job
        db: Sesión de base de datos

    Returns:
        Información del job
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} no encontrado"
        )

    return JobResponse(
        job_id=job.job_id,
        filename=job.filename,
        status=job.status.value,
        total_pages=job.total_pages,
        processed_pages=job.processed_pages,
        documents_created=job.documents_created,
        error_message=job.error_message,
        processing_time=job.processing_time,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Lista todos los jobs

    Args:
        status: Filtrar por estado (opcional)
        limit: Número máximo de resultados
        offset: Offset para paginación
        db: Sesión de base de datos

    Returns:
        Lista de jobs
    """
    query = db.query(Job)

    # Filtrar por estado si se especifica
    if status:
        try:
            job_status = JobStatus(status)
            query = query.filter(Job.status == job_status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido: {status}"
            )

    # Ordenar por fecha de creación (más reciente primero)
    query = query.order_by(Job.created_at.desc())

    # Aplicar paginación
    jobs = query.offset(offset).limit(limit).all()

    return [
        JobResponse(
            job_id=job.job_id,
            filename=job.filename,
            status=job.status.value,
            total_pages=job.total_pages,
            processed_pages=job.processed_pages,
            documents_created=job.documents_created,
            error_message=job.error_message,
            processing_time=job.processing_time,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}/logs", response_model=List[LogResponse])
async def get_job_logs(job_id: str, db: Session = Depends(get_db)):
    """
    Obtiene los logs de un job

    Args:
        job_id: ID del job
        db: Sesión de base de datos

    Returns:
        Lista de logs
    """
    # Verificar que el job existe
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} no encontrado"
        )

    # Obtener logs
    logs = db.query(ProcessingLog)\
        .filter(ProcessingLog.job_id == job_id)\
        .order_by(ProcessingLog.timestamp.asc())\
        .all()

    return [
        LogResponse(
            level=log.level,
            message=log.message,
            timestamp=log.timestamp
        )
        for log in logs
    ]
