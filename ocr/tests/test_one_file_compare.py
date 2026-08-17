# test_one_file_compare.py
"""Test UN SEUL PDF et comparer résultats"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr.ocr_engine import OCREngine
from src.ocr.data_extractor import DataExtractor
from src.config import SAMPLES_DIR

def main():
    print("\n" + "="*70)
    print("COMPARE EXTRACTED vs REAL DATA")
    print("="*70)
    
    # Get first PDF
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))
    if not pdfs:
        print("❌ No PDFs!")
        return
    
    test_pdf = pdfs[0]
    print(f"\n📄 FILE: {test_pdf.name}\n")
    
    # Initialize
    engine = OCREngine()
    extractor = DataExtractor()
    
    # Extract
    print("🔧 Extracting...\n")
    ocr_result = engine.extract_text(test_pdf)
    
    if not ocr_result:
        print("❌ Extraction failed!")
        return
    
    fields = extractor.extract_fields(ocr_result['data'])
    
    # Display results
    print("="*70)
    print("EXTRACTED DATA (from OCR):")
    print("="*70)
    print(f"Supplier:      {fields['fournisseur']}")
    print(f"Invoice #:     {fields['numero_facture']}")
    print(f"Date:          {fields['date']}")
    print(f"Amount HT:     {fields['montant_ht']}")
    print(f"Amount TVA:    {fields['montant_tva']}")
    print(f"Amount TTC:    {fields['montant_ttc']}")
    
    valid, msg = extractor.validate(fields)
    print(f"Validation:    {msg}")
    
    # Instructions
    print("\n" + "="*70)
    print("NOW:")
    print("="*70)
    print(f"1. Open: {test_pdf}")
    print("2. Manually read the values:")
    print("   - Supplier (fournisseur)")
    print("   - Invoice number (N° Facture)")
    print("   - Date (Date Facture)")
    print("   - Amount HT")
    print("   - Amount TVA")
    print("   - Amount TTC")
    print("\n3. Compare with extracted data above")
    print("4. Tell me if they match! ✅ or not ❌")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()