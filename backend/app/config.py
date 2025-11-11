"""
Configuración de la aplicación
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Base de datos
    DATABASE_URL: str = Field(
        default="postgresql://pdfuser:pdfpass@localhost:5432/pdfdb",
        description="URL de conexión a PostgreSQL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexión a Redis"
    )

    # Almacenamiento
    STORAGE_ROOT: Path = Field(
        default=Path("/app/storage"),
        description="Directorio raíz de almacenamiento"
    )

    @property
    def STORAGE_INPUT(self) -> Path:
        """Directorio de entrada"""
        path = self.STORAGE_ROOT / "input"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def STORAGE_OUTPUT(self) -> Path:
        """Directorio de salida"""
        path = self.STORAGE_ROOT / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Zona horaria
    TIMEZONE: str = Field(
        default="America/Guayaquil",
        description="Zona horaria de la aplicación"
    )

    # OCR
    TESSERACT_LANG: str = Field(
        default="spa",
        description="Idioma para Tesseract OCR"
    )

    TESSERACT_CMD: str = Field(
        default="/usr/bin/tesseract",
        description="Ruta al ejecutable de Tesseract"
    )

    # Detección de páginas en blanco
    BLANK_PAGE_THRESHOLD: float = Field(
        default=0.98,
        description="Umbral para detectar páginas en blanco (0-1)"
    )

    # Procesamiento de PDF
    PDF_DPI: int = Field(
        default=300,
        description="DPI para conversión de PDF a imagen"
    )

    # Jobs
    JOB_TIMEOUT: int = Field(
        default=3600,
        description="Timeout para jobs en segundos"
    )

    # API
    MAX_UPLOAD_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100 MB
        description="Tamaño máximo de archivo en bytes"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nivel de logging"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
