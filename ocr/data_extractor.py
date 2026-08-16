# src/ocr/data_extractor.py
"""
Extraction des champs métier à partir du texte brut OCR.

Ce module transforme le texte brut (issu de ocr_engine.py) en un
dictionnaire structuré, avec les noms de champs déjà alignés sur
le schéma de la base de données (voir Data/validation/nettoyage.py) :
    nom_fournisseur, numero_facture, numero_client_marsa,
    date_facture, prix_ht, montant_tva, montant_ttc
"""

import logging
import re

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extrait les champs métier d'une facture à partir du texte OCR."""

    def extract_fields(self, text_data):
        """
        Extrait tous les champs d'une facture.

        Paramètre :
            text_data (list) : liste de dicts {"text": ..., "confidence": ...},
                                telle que retournée par OCREngine.extract_text().

        Retourne :
            dict avec les clés : nom_fournisseur, numero_facture,
            numero_client_marsa, date_facture, prix_ht, montant_tva, montant_ttc
        """
        full_text = " ".join(item["text"] for item in text_data)

        return {
            "nom_fournisseur": self._extract_fournisseur(full_text),
            "numero_facture": self._extract_numero(full_text),
            "numero_client_marsa": self._extract_numero_client(full_text),
            "date_facture": self._extract_date(full_text),
            "prix_ht": self._extract_montant_ht(full_text),
            "montant_tva": self._extract_montant_tva(full_text),
            "montant_ttc": self._extract_montant_ttc(full_text),
        }

    # ------------------------------------------------------------
    # FOURNISSEUR
    # ------------------------------------------------------------
    def _extract_fournisseur(self, text):
        """Reconnaît le nom du fournisseur parmi une liste de motifs connus."""
        patterns = [
            r"maroc\s+telecom",
            r"sodep\s+vpn",
            r"sodep\s+depa",
            r"marsa\s+maroc",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(0).upper()
        return "UNKNOWN"

    # ------------------------------------------------------------
    # NUMÉRO DE FACTURE
    # ------------------------------------------------------------
    def _extract_numero(self, text):
        """
        Numéro de facture : cherche une séquence de 12+ chiffres,
        typiquement précédée de "N° facture" ou "Facture N°".
        """
        patterns = [
            r"(?:n[°#]\s+facture|facture\s+n[°#])\s*:\s*(\d{12,})",
            r"(?:facture\s+n[°#])\s+(\d{12,})",
            r"n[°#]\s+facture\s+(\d{12,})",
            r"(\d{12,})\s+du\s+\d{1,2}/\d{1,2}",  # repli
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                num = m.group(1)
                if any(year in num for year in ["2023", "2024"]):
                    return num
        return None

    # ------------------------------------------------------------
    # NUMÉRO DE CLIENT MARSA MAROC
    # ------------------------------------------------------------
    def _extract_numero_client(self, text):
        """
        Numéro de client : format typique Maroc Telecom, une suite de
        groupes de chiffres séparés par des points, précédée de
        "N° client" ou "Client N°".
        Exemples réels : "7.2571863.16", "5.11104.00.00.100006".
        """
        patterns = [
            r"(?:n[°#]\s*client|client\s*n[°#])\s*:?\s*([\d]+(?:\.[\d]+){1,5})",
            r"(?:n[°#]\s*client|client)\s*:?\s*([\d]+(?:\.[\d]+){1,5})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    # ------------------------------------------------------------
    # DATE DE FACTURE
    # ------------------------------------------------------------
    def _extract_date(self, text):
        """Date au format JJ/MM/AAAA, filtrée sur les années 2023-2024."""
        pattern = r"(\d{1,2})/(\d{1,2})/(\d{4})"
        matches = re.findall(pattern, text)

        for day, month, year in matches:
            if year in ["2023", "2024"]:
                return f"{day}/{month}/{year}"

        if matches:
            day, month, year = matches[0]
            return f"{day}/{month}/{year}"

        return None

    # ------------------------------------------------------------
    # MONTANTS
    # ------------------------------------------------------------
    def _extract_montant_ht(self, text):
        """Montant hors taxes (deviendra 'prix_ht' dans la base)."""
        patterns = [
            r"(?:montant\s+)?ht\s*:\s*(\d+[.,\s]\d{2})",
            r"total\s+dh\s+ht\s+(\d+[.,\s]\d{2})",
            r"(?:montant\s+ht|total\s+ht)\s*(\d+[.,\s]\d{2})",
        ]
        return self._chercher_montant(patterns, text)

    def _extract_montant_tva(self, text):
        """Montant de la TVA."""
        patterns = [
            r"montant\s+tva\s+(?:dh\s+)?\(\s*20\s*%\s*\)\s*:\s*(\d+[.,\s]\d{2})",
            r"tva\s+\(\s*20\s*%\s*\)\s*:\s*(\d+[.,\s]\d{2})",
            r"montant\s+tva\s*(\d+[.,\s]\d{2})",
        ]
        return self._chercher_montant(patterns, text)

    def _extract_montant_ttc(self, text):
        """Montant TTC (deviendra 'montant' dans la base)."""
        patterns = [
            r"(?:montant\s+)?(?:à\s+)?(?:payer\s+)?dh\s+ttc\s*:\s*(\d+[.,\s]\d{2})",
            r"montant\s+ttc\s*:\s*(\d+[.,\s]\d{2})",
            r"ttc\s*:\s*(\d+[.,\s]\d{2})",
            r"total\s+ttc\s*(\d+[.,\s]\d{2})",
        ]
        return self._chercher_montant(patterns, text)

    def _chercher_montant(self, patterns, text):
        """Fonction utilitaire commune : essaie chaque motif jusqu'à trouver un montant valide."""
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(" ", "").replace(",", ".")
                try:
                    return float(val)
                except ValueError:
                    pass
        return None

    # ------------------------------------------------------------
    # VALIDATION INTERNE (contrôle rapide, indépendant de validation.py)
    # ------------------------------------------------------------
    def validate(self, extracted_data):
        """
        Contrôle rapide de cohérence HT + TVA ≈ TTC, réalisé directement
        après l'extraction OCR (avant même le pipeline de validation.py).

        Retourne :
            (True, message)  si cohérent
            (False, message) si incohérent
            (None, message)  si données incomplètes
        """
        ht = extracted_data.get("prix_ht")
        tva = extracted_data.get("montant_tva")
        ttc = extracted_data.get("montant_ttc")

        if ht is not None and tva is not None and ttc is not None:
            calc_ttc = ht + tva
            if abs(calc_ttc - ttc) < 1:
                return True, "Cohérent"
            return False, f"Incohérent : {ht} + {tva} ≠ {ttc}"

        return None, "Données incomplètes"