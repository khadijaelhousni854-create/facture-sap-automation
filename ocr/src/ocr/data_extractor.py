# src/ocr/data_extractor.py
"""Extraction optimisée des 6 champs"""

import logging
import re

logger = logging.getLogger(__name__)

class DataExtractor:
    
    def extract_fields(self, text_data):
        """Extraire les 6 champs"""
        full_text = " ".join([item['text'] for item in text_data])
        
        result = {
            "fournisseur": self._extract_fournisseur(full_text),
            "numero_facture": self._extract_numero(full_text),
            "date": self._extract_date(full_text),
            "montant_ht": self._extract_montant_ht(full_text),
            "montant_tva": self._extract_montant_tva(full_text),
            "montant_ttc": self._extract_montant_ttc(full_text),
        }
        
        return result
    
    def _extract_fournisseur(self, text):
        """Supplier name"""
        patterns = [
            r'maroc\s+telecom',
            r'sodep\s+vpn',
            r'sodep\s+depa',
            r'marsa\s+maroc',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(0).upper()
        return "UNKNOWN"
    
    def _extract_numero(self, text):
        """Invoice number - look for patterns like "0000012064022024" """
        # Pattern: 12+ digits that look like invoice numbers
        patterns = [
            r'(?:n[°#]\s+facture|facture\s+n[°#])\s*:\s*(\d{12,})',
            r'(?:facture\s+n[°#])\s+(\d{12,})',
            r'n[°#]\s+facture\s+(\d{12,})',
            # Fallback: find any 12+ digit sequence
            r'(\d{12,})\s+du\s+\d{1,2}/\d{1,2}',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                num = m.group(1)
                # Verify it looks like invoice number (contains year 2023-2024)
                if any(year in num for year in ['2023', '2024']):
                    return num
        
        return None
    
    def _extract_date(self, text):
        """Date - DD/MM/YYYY but filter out wrong years"""
        # Look for dates in range 2023-2024
        pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        matches = re.findall(pattern, text)
        
        for day, month, year in matches:
            if year in ['2023', '2024']:
                return f"{day}/{month}/{year}"
        
        # Fallback
        if matches:
            day, month, year = matches[0]
            return f"{day}/{month}/{year}"
        
        return None
    
    def _extract_montant_ht(self, text):
        """Amount before tax"""
        patterns = [
            r'(?:montant\s+)?ht\s*:\s*(\d+[.,\s]\d{2})',
            r'total\s+dh\s+ht\s+(\d+[.,\s]\d{2})',
            r'(?:montant\s+ht|total\s+ht)\s*(\d+[.,\s]\d{2})',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(' ', '').replace(',', '.')
                try:
                    return float(val)
                except:
                    pass
        
        return None
    
    def _extract_montant_tva(self, text):
        """Tax amount"""
        patterns = [
            r'montant\s+tva\s+(?:dh\s+)?\(\s*20\s*%\s*\)\s*:\s*(\d+[.,\s]\d{2})',
            r'tva\s+\(\s*20\s*%\s*\)\s*:\s*(\d+[.,\s]\d{2})',
            r'montant\s+tva\s*(\d+[.,\s]\d{2})',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(' ', '').replace(',', '.')
                try:
                    return float(val)
                except:
                    pass
        
        return None
    
    def _extract_montant_ttc(self, text):
        """Total amount"""
        patterns = [
            r'(?:montant\s+)?(?:à\s+)?(?:payer\s+)?dh\s+ttc\s*:\s*(\d+[.,\s]\d{2})',
            r'montant\s+ttc\s*:\s*(\d+[.,\s]\d{2})',
            r'ttc\s*:\s*(\d+[.,\s]\d{2})',
            r'total\s+ttc\s*(\d+[.,\s]\d{2})',
        ]
        
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(' ', '').replace(',', '.')
                try:
                    return float(val)
                except:
                    pass
        
        return None
    
    def validate(self, extracted_data):
        """Validate data consistency"""
        ht = extracted_data.get('montant_ht')
        tva = extracted_data.get('montant_tva')
        ttc = extracted_data.get('montant_ttc')
        
        if ht and tva and ttc:
            calc_ttc = ht + tva
            if abs(calc_ttc - ttc) < 1:
                return True, "✅ Valid"
            else:
                return False, f"❌ Invalid: {ht}+{tva}≠{ttc}"
        
        return None, "⚠️ Incomplete"
