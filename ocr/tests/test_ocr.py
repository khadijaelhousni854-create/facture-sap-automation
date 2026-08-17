# tests/test_ocr.py
"""Test OCR Engine with real PDFs"""

import sys
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr.ocr_engine import OCREngine
from src.config import SAMPLES_DIR

def test_ocr_basic():
    """Test basic OCR extraction"""
    
    print("=== Testing OCR Engine ===\n")
    
    # Initialize engine
    print("🔧 Initializing OCREngine...")
    engine = OCREngine()
    print("✅ OCREngine ready\n")
    
    # Find PDFs
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))
    print(f"📋 Found {len(pdfs)} PDFs\n")
    
    if not pdfs:
        print("❌ No PDFs found in data/samples/")
        return
    
    # Test on first 3 PDFs
    for pdf_file in pdfs[:3]:
        print(f"--- Testing: {pdf_file.name} ---")
        
        try:
            # Extract text
            result = engine.extract_text(pdf_file)
            
            if result:
                print(f"✅ Extraction successful")
                print(f"   Elements found: {result['elements']}")
                print(f"   First 3 texts:")
                for item in result['data'][:3]:
                    print(f"      • {item['text'][:50]}")
            else:
                print(f"❌ Extraction failed")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

if __name__ == "__main__":
    test_ocr_basic()
