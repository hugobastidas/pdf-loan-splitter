"""
Funciones auxiliares
"""
import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import pytz
from app.config import settings


def generate_job_id() -> str:
    """
    Genera un ID único para un job
    """
    return f"job_{uuid.uuid4().hex[:12]}"


def generate_document_id() -> str:
    """
    Genera un ID único para un documento
    """
    return f"doc_{uuid.uuid4().hex[:12]}"


def get_current_time() -> datetime:
    """
    Obtiene la hora actual en la zona horaria configurada
    """
    tz = pytz.timezone(settings.TIMEZONE)
    return datetime.now(tz)


def calculate_file_hash(file_path: Path) -> str:
    """
    Calcula el hash SHA256 de un archivo
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres peligrosos
    """
    # Remover caracteres peligrosos
    dangerous_chars = ['/', '\\', '..', '\x00', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Limitar longitud
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]

    return f"{name}{ext}"


def format_processing_time(seconds: float) -> str:
    """
    Formatea el tiempo de procesamiento en formato legible
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def ensure_dir(path: Path) -> Path:
    """
    Asegura que un directorio exista, creándolo si es necesario
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
