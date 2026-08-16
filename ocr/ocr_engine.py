# src/ocr/ocr_engine.py
"""
Moteur OCR — extraction du texte brut d'une facture PDF avec EasyOCR.

Rôle : lire un PDF, le convertir en image, puis extraire tout le texte
visible avec ses coordonnées et son niveau de confiance. Ce module ne
fait AUCUNE interprétation métier — il retourne juste le texte brut,
que data_extractor.py viendra ensuite analyser.
"""

import logging
from pathlib import Path

import easyocr
import pymupdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCREngine:
    """Moteur d'extraction de texte à partir de fichiers PDF."""

    def __init__(self):
        logger.info("Initialisation du moteur EasyOCR (français)...")
        self.reader = easyocr.Reader(["fr"])
        logger.info("EasyOCR prêt.")

    def extract_text(self, pdf_path):
        """
        Extrait le texte brut d'un PDF (1ère page uniquement).

        Paramètre :
            pdf_path (str | Path) : chemin vers le fichier PDF.

        Retourne :
            dict : {
                "filename": nom du fichier,
                "status": "success" | "error",
                "elements": nombre de blocs de texte trouvés,
                "data": [{"text": ..., "confidence": ...}, ...]
            }
            None si une erreur survient.
        """
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"Lecture du fichier : {pdf_path.name}")

            doc = pymupdf.open(str(pdf_path))
            page = doc[0]
            pix = page.get_pixmap()

            img_path = "temp.png"
            pix.save(img_path)

            resultats_bruts = self.reader.readtext(img_path)

            text_data = [
                {"text": texte, "confidence": float(confiance)}
                for (_bbox, texte, confiance) in resultats_bruts
            ]

            doc.close()

            logger.info(f"{len(text_data)} éléments de texte extraits.")

            return {
                "filename": pdf_path.name,
                "status": "success",
                "elements": len(text_data),
                "data": text_data,
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction OCR : {e}")
            return None

