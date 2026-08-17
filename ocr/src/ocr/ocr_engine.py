# src/ocr/ocr_engine.py
"""Moteur OCR avec EasyOCR - simple et robuste"""

import logging
from pathlib import Path
import easyocr
import pymupdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCREngine:
    """Classe OCR pour traiter des PDFs"""
    
    def __init__(self):
        logger.info("🔧 Initialisation EasyOCR...")
        self.reader = easyocr.Reader(['fr'])
        logger.info("✅ EasyOCR prêt")
    
    def extract_text(self, pdf_path):
        """Extraire texte d'un PDF"""
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"📄 Lecture: {pdf_path.name}")
            
            doc = pymupdf.open(str(pdf_path))
            page = doc[0]
            pix = page.get_pixmap()
            
            img_path = "temp.png"
            pix.save(img_path)
            
            results = self.reader.readtext(img_path)
            
            text_data = []
            for result in results:
                text_data.append({
                    "text": result[1],
                    "confidence": float(result[2])
                })
            
            doc.close()
            
            logger.info(f"✅ {len(text_data)} éléments extraits")
            
            return {
                "filename": pdf_path.name,
                "status": "success",
                "elements": len(text_data),
                "data": text_data
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return None

def main():
    """Test simple"""
    engine = OCREngine()
    
    from src.config import SAMPLES_DIR
    
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))
    if pdfs:
        logger.info(f"📋 Test sur: {pdfs[0].name}")
        result = engine.extract_text(pdfs[0])
        if result and result['elements'] > 0:
            logger.info(f"✅ {result['elements']} éléments trouvés!")

if __name__ == "__main__":
    main()
