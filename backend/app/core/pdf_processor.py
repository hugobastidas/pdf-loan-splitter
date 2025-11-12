"""
Procesador de PDF con OCR, detección de código de barras y división
"""
import io
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
import pytesseract
from pyzbar import pyzbar
from app.config import settings
from app.db.models import DocumentType

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Procesador principal de PDFs
    """

    def __init__(self):
        """Inicializa el procesador"""
        # Configurar tesseract
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        self.dpi = settings.PDF_DPI
        self.blank_threshold = settings.BLANK_PAGE_THRESHOLD
        self.tesseract_lang = settings.TESSERACT_LANG

    def convert_pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """
        Convierte un PDF a lista de imágenes

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Lista de imágenes PIL
        """
        logger.info(f"Convirtiendo PDF a imágenes: {pdf_path}")
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='png'
            )
            logger.info(f"PDF convertido a {len(images)} imágenes")
            return images
        except Exception as e:
            logger.error(f"Error al convertir PDF a imágenes: {e}")
            raise

    def is_blank_page(self, image: Image.Image) -> bool:
        """
        Detecta si una página está en blanco

        Args:
            image: Imagen PIL de la página

        Returns:
            True si la página está en blanco
        """
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

            # Calcular el porcentaje de píxeles blancos
            total_pixels = gray.size
            white_pixels = np.sum(gray > 240)  # Umbral para considerar blanco
            white_ratio = white_pixels / total_pixels

            is_blank = white_ratio >= self.blank_threshold
            logger.debug(f"Página blanca: {is_blank} (ratio: {white_ratio:.2f})")
            return is_blank
        except Exception as e:
            logger.error(f"Error al detectar página en blanco: {e}")
            return False

    def detect_barcode(self, image: Image.Image) -> Optional[Dict[str, str]]:
        """
        Detecta código de barras en una imagen

        Args:
            image: Imagen PIL de la página

        Returns:
            Dict con 'value' y 'type' del código, o None si no se detecta
        """
        try:
            # Convertir a formato numpy para pyzbar
            img_array = np.array(image)

            # Detectar códigos de barras
            barcodes = pyzbar.decode(img_array)

            if barcodes:
                # Tomar el primer código encontrado
                barcode = barcodes[0]
                value = barcode.data.decode('utf-8')
                barcode_type = barcode.type

                logger.info(f"Código de barras detectado: {value} (tipo: {barcode_type})")
                return {
                    'value': value,
                    'type': barcode_type
                }

            return None
        except Exception as e:
            logger.error(f"Error al detectar código de barras: {e}")
            return None

    def extract_text_ocr(self, image: Image.Image) -> str:
        """
        Extrae texto de una imagen usando OCR

        Args:
            image: Imagen PIL de la página

        Returns:
            Texto extraído
        """
        try:
            # Aplicar OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.tesseract_lang,
                config='--psm 3'  # Automatic page segmentation
            )

            logger.debug(f"Texto extraído por OCR: {len(text)} caracteres")
            return text.strip()
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return ""

    def classify_document(self, barcode_value: Optional[str] = None,
                         ocr_text: Optional[str] = None) -> DocumentType:
        """
        Clasifica un documento basado en el código de barras o texto OCR

        Args:
            barcode_value: Valor del código de barras
            ocr_text: Texto extraído por OCR

        Returns:
            Tipo de documento
        """
        # Priorizar clasificación por código de barras
        if barcode_value:
            barcode_upper = barcode_value.upper()

            if 'CEDULA' in barcode_upper or 'CED' in barcode_upper:
                return DocumentType.CEDULA
            elif 'CERTIFICADO' in barcode_upper or 'CERT' in barcode_upper:
                return DocumentType.CERTIFICADO
            elif 'PAPELETA' in barcode_upper or 'VOTACION' in barcode_upper:
                return DocumentType.PAPELETA_VOTACION
            elif 'MECANIZADO' in barcode_upper or 'MEC' in barcode_upper:
                return DocumentType.MECANIZADO
            elif 'PLANILLA' in barcode_upper or 'SERVICIOS' in barcode_upper:
                return DocumentType.PLANILLA_SERVICIOS
            elif 'CUENTA' in barcode_upper:
                return DocumentType.CERTIFICADO_CUENTA

        # Clasificación por OCR si no hay código de barras
        if ocr_text:
            ocr_upper = ocr_text.upper()

            keywords = {
                DocumentType.CEDULA: ['CEDULA', 'IDENTIDAD', 'REGISTRO CIVIL'],
                DocumentType.CERTIFICADO: ['CERTIFICADO', 'CERTIFICA'],
                DocumentType.PAPELETA_VOTACION: ['PAPELETA', 'VOTACION', 'ELECTORAL'],
                DocumentType.MECANIZADO: ['MECANIZADO', 'IESS'],
                DocumentType.PLANILLA_SERVICIOS: ['PLANILLA', 'SERVICIOS', 'LUZ', 'AGUA'],
                DocumentType.CERTIFICADO_CUENTA: ['CERTIFICADO', 'CUENTA', 'BANCARIO', 'BANCO']
            }

            # Buscar keywords en el texto
            for doc_type, words in keywords.items():
                if any(word in ocr_upper for word in words):
                    return doc_type

        return DocumentType.UNKNOWN

    def analyze_pages(self, images: List[Image.Image]) -> List[Dict]:
        """
        Analiza todas las páginas del PDF

        Args:
            images: Lista de imágenes de las páginas

        Returns:
            Lista de diccionarios con información de cada página
        """
        pages_info = []

        for idx, image in enumerate(images):
            page_num = idx + 1
            logger.info(f"Analizando página {page_num}/{len(images)}")

            # Verificar si es blanco
            is_blank = self.is_blank_page(image)

            if is_blank:
                pages_info.append({
                    'page_number': page_num,
                    'is_blank': True,
                    'barcode': None,
                    'ocr_text': None,
                    'is_separator': False
                })
                continue

            # Detectar código de barras
            barcode = self.detect_barcode(image)

            # Si hay código de barras, es un separador
            is_separator = barcode is not None

            # Extraer texto OCR solo si no hay código de barras
            ocr_text = None
            if not barcode:
                ocr_text = self.extract_text_ocr(image)

            pages_info.append({
                'page_number': page_num,
                'is_blank': False,
                'barcode': barcode,
                'ocr_text': ocr_text,
                'is_separator': is_separator
            })

        return pages_info

    def split_pdf_by_separators(self, pdf_path: Path, pages_info: List[Dict],
                                output_dir: Path) -> List[Dict]:
        """
        Divide el PDF en subdocumentos basándose en páginas separadoras

        Args:
            pdf_path: Ruta al PDF original
            pages_info: Información de las páginas
            output_dir: Directorio de salida

        Returns:
            Lista de documentos creados con sus metadatos
        """
        logger.info(f"Dividiendo PDF en subdocumentos")

        # Leer el PDF original
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        # Encontrar índices de separadores
        separator_indices = [
            i for i, info in enumerate(pages_info)
            if info['is_separator']
        ]

        logger.info(f"Encontrados {len(separator_indices)} separadores")

        # Si no hay separadores, tratar todo el documento como uno solo
        if not separator_indices:
            logger.warning("No se encontraron separadores, procesando como documento único")
            return self._create_single_document(
                reader, pages_info, output_dir, pdf_path.stem
            )

        # Dividir por separadores
        documents = []

        for idx, sep_idx in enumerate(separator_indices):
            # Determinar rango de páginas para este documento
            start_idx = sep_idx

            # El final es el siguiente separador o el final del documento
            if idx + 1 < len(separator_indices):
                end_idx = separator_indices[idx + 1] - 1
            else:
                end_idx = total_pages - 1

            # Extraer páginas (excluyendo blancos)
            doc_info = self._extract_document(
                reader, pages_info, start_idx, end_idx,
                output_dir, pdf_path.stem, idx + 1
            )

            if doc_info:
                documents.append(doc_info)

        logger.info(f"Creados {len(documents)} subdocumentos")
        return documents

    def _create_single_document(self, reader: PdfReader, pages_info: List[Dict],
                               output_dir: Path, base_name: str) -> List[Dict]:
        """
        Crea un único documento cuando no hay separadores
        """
        writer = PdfWriter()
        blank_count = 0
        ocr_texts = []

        for idx, info in enumerate(pages_info):
            if info['is_blank']:
                blank_count += 1
                continue

            writer.add_page(reader.pages[idx])

            if info['ocr_text']:
                ocr_texts.append(info['ocr_text'])

        # Guardar documento
        output_path = output_dir / f"{base_name}_doc_1.pdf"
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        # Clasificar documento
        combined_ocr = ' '.join(ocr_texts)
        doc_type = self.classify_document(ocr_text=combined_ocr)

        return [{
            'filename': output_path.name,
            'file_path': str(output_path),
            'page_start': 1,
            'page_end': len(reader.pages),
            'total_pages': len(writer.pages),
            'has_blank_pages': blank_count,
            'barcode_value': None,
            'barcode_type': None,
            'document_type': doc_type,
            'ocr_text': combined_ocr[:1000] if combined_ocr else None  # Limitar tamaño
        }]

    def _extract_document(self, reader: PdfReader, pages_info: List[Dict],
                         start_idx: int, end_idx: int, output_dir: Path,
                         base_name: str, doc_num: int) -> Optional[Dict]:
        """
        Extrae un subdocumento del PDF original
        """
        writer = PdfWriter()
        blank_count = 0
        ocr_texts = []
        barcode_info = pages_info[start_idx]['barcode']

        # Agregar páginas (excluyendo la página separadora y blancos)
        for idx in range(start_idx + 1, end_idx + 1):
            if idx >= len(pages_info):
                break

            info = pages_info[idx]

            if info['is_blank']:
                blank_count += 1
                continue

            writer.add_page(reader.pages[idx])

            if info['ocr_text']:
                ocr_texts.append(info['ocr_text'])

        # Si no hay páginas, no crear el documento
        if len(writer.pages) == 0:
            logger.warning(f"Documento {doc_num} no tiene páginas, omitiendo")
            return None

        # Guardar documento
        output_path = output_dir / f"{base_name}_doc_{doc_num}.pdf"
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        # Clasificar documento
        combined_ocr = ' '.join(ocr_texts)
        barcode_value = barcode_info['value'] if barcode_info else None
        doc_type = self.classify_document(
            barcode_value=barcode_value,
            ocr_text=combined_ocr
        )

        return {
            'filename': output_path.name,
            'file_path': str(output_path),
            'page_start': start_idx + 2,  # +2 porque saltamos separador y es 1-indexed
            'page_end': end_idx + 1,
            'total_pages': len(writer.pages),
            'has_blank_pages': blank_count,
            'barcode_value': barcode_value,
            'barcode_type': barcode_info['type'] if barcode_info else None,
            'document_type': doc_type,
            'ocr_text': combined_ocr[:1000] if combined_ocr else None  # Limitar tamaño
        }

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> Dict:
        """
        Procesa un PDF completo

        Args:
            pdf_path: Ruta al archivo PDF
            output_dir: Directorio de salida

        Returns:
            Diccionario con resultados del procesamiento
        """
        logger.info(f"Iniciando procesamiento de PDF: {pdf_path}")

        try:
            # Convertir a imágenes
            images = self.convert_pdf_to_images(pdf_path)
            total_pages = len(images)

            # Analizar páginas
            pages_info = self.analyze_pages(images)

            # Dividir PDF
            documents = self.split_pdf_by_separators(
                pdf_path, pages_info, output_dir
            )

            result = {
                'success': True,
                'total_pages': total_pages,
                'documents': documents,
                'blank_pages': sum(1 for p in pages_info if p['is_blank']),
                'separators': sum(1 for p in pages_info if p['is_separator'])
            }

            logger.info(f"Procesamiento completado: {len(documents)} documentos creados")
            return result

        except Exception as e:
            logger.error(f"Error al procesar PDF: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total_pages': 0,
                'documents': []
            }
