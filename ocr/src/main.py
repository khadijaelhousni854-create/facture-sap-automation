# src/main.py
"""Orchestration - lance le pipeline complet"""

import logging
import json
from pathlib import Path
from ocr.ocr_engine import OCREngine
from ocr.data_extractor import DataExtractor
from config import SAMPLES_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_all_invoices():
    """Traiter tous les PDFs dans data/samples/"""
    
    logger.info("🚀 Démarrage pipeline...")
    
    engine = OCREngine()
    extractor = DataExtractor()
    
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))
    logger.info(f"📋 {len(pdfs)} PDFs trouvés")
    
    results = []
    
    for pdf_path in pdfs[:3]:  # Test sur 3 PDFs
        logger.info(f"\n--- Traitement: {pdf_path.name} ---")
        
        # OCR
        ocr_result = engine.extract_text(pdf_path)
        if not ocr_result:
            logger.error(f"❌ OCR failed")
            continue
        
        # Extract fields
        fields = extractor.extract_fields(ocr_result['data'])
        
        # Validate
        valid, msg = extractor.validate(fields)
        
        result = {
            "filename": pdf_path.name,
            "ocr_elements": ocr_result['elements'],
            "extracted_fields": fields,
            "validation": msg
        }
        
        results.append(result)
        logger.info(f"✅ Résultat: {fields['fournisseur']} - {fields['numero_facture']}")
    
    # Save results to JSON
    output_file = OUTPUT_DIR / "extracted_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ Résultats sauvegardés: {output_file}")
    
    return results

if __name__ == "__main__":
    process_all_invoices()
