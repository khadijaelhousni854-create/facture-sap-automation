"""
ocr_engine.py — Moteur OCR : extraction du texte brut d'une facture PDF.

Ce module ne fait AUCUNE interprétation métier — il retourne juste le
texte brut avec les scores de confiance, que data_extractor.py analyse
ensuite.

FIX MULTI-PAGES : certains PDF contiennent plusieurs factures sur des
pages différentes (ex: facture_ADSL_mois_12_2023.pdf = 2 factures,
2 formats différents, sur 2 pages). L'ancienne version ne lisait que
doc[0] (1ère page) et ignorait silencieusement le reste.
On boucle maintenant sur TOUTES les pages, et on retourne une liste de
résultats (un par page).
"""

import logging
import uuid
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

    def extract_text(self, pdf_path, zoom: float = 3.0):
        """
        Extrait le texte brut de TOUTES les pages d'un PDF.

        zoom=3 -> ~216 DPI (recommandé). Augmenter à 4 ou 5 si l'OCR
        reste peu fiable sur certaines factures.

        Retourne :
            dict : {
                "filename": nom du fichier,
                "status": "success" | "error",
                "nb_pages": nombre de pages traitées,
                "pages": [
                    {
                        "page_index": 0,
                        "elements": nombre de blocs de texte trouvés,
                        "data": [{"text": ..., "confidence": ...}, ...]
                    },
                    ...
                ]
            }
            None si une erreur survient.
        """
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"Lecture du fichier : {pdf_path.name} (zoom={zoom})")

            doc = pymupdf.open(str(pdf_path))
            matrice = pymupdf.Matrix(zoom, zoom)
            pages_resultats = []

            for index_page in range(len(doc)):
                page = doc[index_page]
                pix = page.get_pixmap(matrix=matrice)

                # Nom de fichier temporaire unique (évite les collisions
                # entre pages et entre factures traitées à la suite)
                img_path = Path(f"temp_{pdf_path.stem}_p{index_page}_{uuid.uuid4().hex[:8]}.png")
                try:
                    pix.save(str(img_path))
                    resultats_bruts = self.reader.readtext(str(img_path))
                finally:
                    if img_path.exists():
                        img_path.unlink()

                text_data = [
                    {"text": texte, "confidence": float(confiance)}
                    for (_bbox, texte, confiance) in resultats_bruts
                ]

                logger.info(f"Page {index_page} : {len(text_data)} éléments extraits.")

                pages_resultats.append({
                    "page_index": index_page,
                    "elements": len(text_data),
                    "data": text_data,
                })

            doc.close()

            return {
                "filename": pdf_path.name,
                "status": "success",
                "nb_pages": len(pages_resultats),
                "pages": pages_resultats,
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction OCR : {e}")
            return None