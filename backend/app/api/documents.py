"""
Endpoint para consulta de documentos procesados
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from app.db.database import get_db
from app.db.models import Document, Job, DocumentType

router = APIRouter()


class DocumentResponse(BaseModel):
    """Respuesta de información de documento"""
    id: int
    job_id: str
    document_type: str
    barcode_value: Optional[str]
    barcode_type: Optional[str]
    filename: str
    page_start: int
    page_end: int
    total_pages: int
    has_blank_pages: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    job_id: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Lista documentos procesados

    Args:
        job_id: Filtrar por job (opcional)
        document_type: Filtrar por tipo de documento (opcional)
        limit: Número máximo de resultados
        offset: Offset para paginación
        db: Sesión de base de datos

    Returns:
        Lista de documentos
    """
    query = db.query(Document).join(Job)

    # Filtrar por job_id si se especifica
    if job_id:
        query = query.filter(Job.job_id == job_id)

    # Filtrar por tipo de documento si se especifica
    if document_type:
        try:
            doc_type = DocumentType(document_type)
            query = query.filter(Document.document_type == doc_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de documento inválido: {document_type}"
            )

    # Ordenar por fecha de creación (más reciente primero)
    query = query.order_by(Document.created_at.desc())

    # Aplicar paginación
    documents = query.offset(offset).limit(limit).all()

    return [
        DocumentResponse(
            id=doc.id,
            job_id=doc.job.job_id,
            document_type=doc.document_type.value,
            barcode_value=doc.barcode_value,
            barcode_type=doc.barcode_type,
            filename=doc.filename,
            page_start=doc.page_start,
            page_end=doc.page_end,
            total_pages=doc.total_pages,
            has_blank_pages=doc.has_blank_pages,
            created_at=doc.created_at
        )
        for doc in documents
    ]


@router.get("/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Obtiene información detallada de un documento

    Args:
        document_id: ID del documento
        db: Sesión de base de datos

    Returns:
        Información del documento incluyendo OCR
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Documento {document_id} no encontrado"
        )

    return {
        "id": document.id,
        "job_id": document.job.job_id,
        "document_type": document.document_type.value,
        "barcode_value": document.barcode_value,
        "barcode_type": document.barcode_type,
        "filename": document.filename,
        "file_path": document.file_path,
        "page_start": document.page_start,
        "page_end": document.page_end,
        "total_pages": document.total_pages,
        "has_blank_pages": document.has_blank_pages,
        "ocr_text": document.ocr_text,
        "created_at": document.created_at
    }


@router.get("/documents/{document_id}/download")
async def download_document(document_id: int, db: Session = Depends(get_db)):
    """
    Descarga un documento procesado

    Args:
        document_id: ID del documento
        db: Sesión de base de datos

    Returns:
        Archivo PDF
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Documento {document_id} no encontrado"
        )

    file_path = Path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado en el sistema"
        )

    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=document.filename
    )
