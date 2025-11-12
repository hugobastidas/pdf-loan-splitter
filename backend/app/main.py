"""
Aplicación principal FastAPI
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db
from app.api import upload, jobs, documents

# Configurar logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación
    """
    # Startup
    logger.info("Iniciando aplicación PDF Classifier")
    logger.info(f"Zona horaria: {settings.TIMEZONE}")
    logger.info(f"Storage root: {settings.STORAGE_ROOT}")

    # Inicializar base de datos
    try:
        init_db()
        logger.info("Base de datos inicializada")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")

    # Asegurar que los directorios de storage existen
    settings.STORAGE_INPUT.mkdir(parents=True, exist_ok=True)
    settings.STORAGE_OUTPUT.mkdir(parents=True, exist_ok=True)
    logger.info("Directorios de almacenamiento verificados")

    yield

    # Shutdown
    logger.info("Cerrando aplicación PDF Classifier")


# Crear aplicación FastAPI
app = FastAPI(
    title="PDF Classifier API",
    description="API para clasificación y división de PDFs con códigos de barras",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])


@app.get("/")
async def root():
    """
    Endpoint raíz
    """
    return {
        "name": "PDF Classifier API",
        "version": "1.0.0",
        "status": "running",
        "timezone": settings.TIMEZONE
    }


@app.get("/health")
async def health():
    """
    Health check
    """
    return {
        "status": "healthy",
        "storage_input": str(settings.STORAGE_INPUT),
        "storage_output": str(settings.STORAGE_OUTPUT)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
