# ocr/test_all_invoices.py
"""
Test TOUS les 16 PDFs - PDFs dans Documents/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr_engine import OCREngine
from data_extractor import DataExtractor
import json

def print_table_header():
    print("\n" + "="*160)
    print(f"{'FILE':<35} | {'P':<2} | {'FOURNISSEUR':<18} | {'NUMERO':<16} | {'DATE':<12} | {'HT':<11} | {'TVA':<11} | {'TTC':<11} | {'VALID':<8}")
    print("="*160)

def format_value(val):
    if val is None:
        return "NULL❌"
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)[:14]

def main():
    print("\n🚀 TESTING ALL INVOICES FROM Documents/")
    print("="*160)
    
    # PDFs sont dans Documents/ (au même niveau que ocr/)
    samples_dir = Path(__file__).parent.parent / "Documents"
    
    pdfs = sorted(list(samples_dir.glob("*.pdf")))
    
    if not pdfs:
        print(f"❌ No PDFs found in {samples_dir}")
        print(f"Current script: {Path(__file__)}")
        print(f"Looking in: {samples_dir}")
        print(f"Dir exists: {samples_dir.exists()}")
        if samples_dir.exists():
            print(f"Contents: {list(samples_dir.iterdir())[:5]}")
        return
    
    print(f"Found: {len(pdfs)} PDFs\n")
    
    # Initialize
    try:
        engine = OCREngine()
        extractor = DataExtractor()
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    all_results = []
    print_table_header()
    
    # Process each PDF
    for pdf_idx, pdf_path in enumerate(pdfs, 1):
        try:
            ocr_result = engine.extract_text(pdf_path)
            
            if not ocr_result or ocr_result['status'] != 'success':
                print(f"{pdf_path.name:<35} | ERROR: OCR FAILED")
                continue
            
            nb_pages = ocr_result['nb_pages']
            for page_info in ocr_result['pages']:
                page_index = page_info['page_index']
                
                fields = extractor.extract_fields(page_info['data'])
                valid, msg = extractor.validate(fields)
                
                status = "✅" if valid else "❌"
                
                result_row = {
                    'filename': pdf_path.name,
                    'page_index': page_index,
                    'nb_pages': nb_pages,
                    'fournisseur': fields['fournisseur'],
                    'numero_facture': fields['numero_facture'],
                    'date': fields['date'],
                    'montant_ht': fields['montant_ht'],
                    'montant_tva': fields['montant_tva'],
                    'montant_ttc': fields['montant_ttc'],
                    'validation_msg': msg,
                    'is_valid': valid,
                }
                
                all_results.append(result_row)
                
                if page_index == 0:
                    file_label = pdf_path.name
                else:
                    file_label = f"  └─page {page_index}"
                
                print(
                    f"{file_label:<35} | "
                    f"{page_index:<2} | "
                    f"{format_value(fields['fournisseur']):<18} | "
                    f"{format_value(fields['numero_facture']):<16} | "
                    f"{format_value(fields['date']):<12} | "
                    f"{format_value(fields['montant_ht']):<11} | "
                    f"{format_value(fields['montant_tva']):<11} | "
                    f"{format_value(fields['montant_ttc']):<11} | "
                    f"{status:<8}"
                )
        
        except Exception as e:
            print(f"{pdf_path.name:<35} | ERROR: {str(e)[:50]}")
            import traceback
            traceback.print_exc()
    
    print("="*160)
    
    total = len(all_results)
    valid_count = sum(1 for r in all_results if r['is_valid'])
    null_numero = sum(1 for r in all_results if r['numero_facture'] is None)
    null_ht = sum(1 for r in all_results if r['montant_ht'] is None)
    null_tva = sum(1 for r in all_results if r['montant_tva'] is None)
    null_ttc = sum(1 for r in all_results if r['montant_ttc'] is None)
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total records: {total}")
    print(f"  ✅ Valid: {valid_count}/{total} ({100*valid_count/total:.1f}%)" if total > 0 else "  ✅ Valid: 0/0")
    print(f"\n❌ MISSING FIELDS:")
    print(f"  Numero: {null_numero}")
    print(f"  HT: {null_ht}")
    print(f"  TVA: {null_tva}")
    print(f"  TTC: {null_ttc}")
    
    # Save JSON
    output_file = Path(__file__).parent.parent / "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results: {output_file}")
    
    # Show problems
    problems = [r for r in all_results if not r['is_valid']]
    if problems:
        print(f"\n🔍 PROBLEMS ({len(problems)} records):")
        for i, p in enumerate(problems[:5], 1):
            print(f"\n{i}. {p['filename']} (page {p['page_index']}):")
            print(f"   Numero: {p['numero_facture']}")
            print(f"   HT: {p['montant_ht']}")
            print(f"   TVA: {p['montant_tva']}")
            print(f"   TTC: {p['montant_ttc']}")

if __name__ == "__main__":
    main()