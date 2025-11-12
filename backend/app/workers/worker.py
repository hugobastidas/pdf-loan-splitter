"""
Worker RQ para procesamiento asíncrono de PDFs
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from redis import Redis
from rq import Worker, Queue, Connection
from sqlalchemy.orm import Session
from app.config import settings
from app.core.pdf_processor import PDFProcessor
from app.core.utils import ensure_dir
from app.db.database import SessionLocal, engine
from app.db.models import Job, Document, JobStatus, ProcessingLog

# Configurar logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_pdf_job(job_id: str, filename: str, file_path: str):
    """
    Procesa un PDF de forma asíncrona

    Args:
        job_id: ID del job
        filename: Nombre del archivo
        file_path: Ruta al archivo PDF
    """
    db = SessionLocal()
    start_time = time.time()

    try:
        logger.info(f"Iniciando procesamiento de job {job_id}")

        # Buscar el job en la base de datos
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} no encontrado en la base de datos")
            return

        # Actualizar estado a PROCESSING
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        # Log inicial
        log_processing(db, job_id, "INFO", f"Iniciando procesamiento de {filename}")

        # Crear directorio de salida para este job
        output_dir = ensure_dir(settings.STORAGE_OUTPUT / job_id)

        # Procesar el PDF
        processor = PDFProcessor()
        pdf_path = Path(file_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        result = processor.process_pdf(pdf_path, output_dir)

        if not result['success']:
            raise Exception(result.get('error', 'Error desconocido'))

        # Actualizar job con información del procesamiento
        job.total_pages = result['total_pages']
        job.processed_pages = result['total_pages']
        job.documents_created = len(result['documents'])

        # Guardar documentos en la base de datos
        for doc_info in result['documents']:
            document = Document(
                job_id=job.id,
                document_type=doc_info['document_type'],
                barcode_value=doc_info.get('barcode_value'),
                barcode_type=doc_info.get('barcode_type'),
                filename=doc_info['filename'],
                file_path=doc_info['file_path'],
                page_start=doc_info['page_start'],
                page_end=doc_info['page_end'],
                total_pages=doc_info['total_pages'],
                has_blank_pages=doc_info.get('has_blank_pages', 0),
                ocr_text=doc_info.get('ocr_text')
            )
            db.add(document)

        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        job.processing_time = processing_time
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

        db.commit()

        logger.info(
            f"Job {job_id} completado exitosamente. "
            f"Documentos creados: {len(result['documents'])}. "
            f"Tiempo: {processing_time:.2f}s"
        )

        log_processing(
            db, job_id, "INFO",
            f"Procesamiento completado. {len(result['documents'])} documentos creados "
            f"en {processing_time:.2f}s"
        )

    except Exception as e:
        logger.error(f"Error al procesar job {job_id}: {e}", exc_info=True)

        # Actualizar job con error
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            processing_time = time.time() - start_time
            job.processing_time = processing_time
            db.commit()

        log_processing(db, job_id, "ERROR", f"Error en procesamiento: {str(e)}")

    finally:
        db.close()


def log_processing(db: Session, job_id: str, level: str, message: str):
    """
    Registra un log de procesamiento

    Args:
        db: Sesión de base de datos
        job_id: ID del job
        level: Nivel del log (INFO, WARNING, ERROR)
        message: Mensaje del log
    """
    try:
        log = ProcessingLog(
            job_id=job_id,
            level=level,
            message=message
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Error al guardar log: {e}")


def run_worker():
    """
    Ejecuta el worker RQ
    """
    redis_conn = Redis.from_url(settings.REDIS_URL)

    with Connection(redis_conn):
        worker = Worker(['default'], connection=redis_conn)
        logger.info("Worker RQ iniciado, esperando trabajos...")
        worker.work()


if __name__ == '__main__':
    run_worker()
