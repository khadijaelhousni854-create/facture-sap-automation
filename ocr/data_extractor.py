"""
data_extractor.py — Extraction des champs métier à partir du texte OCR.

Sortie alignée sur les clés attendues par nettoyage.nettoyer_facture() :
    nom_fournisseur, numero_facture, numero_client_marsa, date_facture,
    periode_facturation, prix_ht, montant

Gère 2 formats de factures connus :
  Format A ("Abonnement Internet Mobile") :
      N° Client : ... / N° Facture : ... / Date Facture : ...
      Montant HT : / Montant TVA ( Taux de 20% ) : / Montant TTC :

  Format B ("Facture n°... du... / Mois :...") :
      Facture n° NUM du DATE / N° client : ...
      Total DH HT / Montant TVA DH ( 20% ) / Montant à payer DH TTC
"""

import re

# Montant : accepte un séparateur de milliers (espace) et "," ou "." en décimal
MONTANT_RE = re.compile(r"(\d{1,3}(?:[ ]\d{3})*[.,]\d{2})")


class DataExtractor:
    """Extrait les champs métier d'une facture à partir du texte OCR."""

    def extract_fields(self, text_data):
        full_text = " ".join(item["text"] for item in text_data)

        return {
            "nom_fournisseur": self._extract_fournisseur(full_text),
            "numero_facture": self._extract_numero(full_text),
            "numero_client_marsa": self._extract_numero_client(full_text),
            "date_facture": self._extract_date(full_text),
            "periode_facturation": self._extract_periode(full_text),
            "prix_ht": self._extract_montant_ht(full_text),
            "montant": self._extract_montant_ttc(full_text),      # clé "montant" (TTC)
            "montant_tva": self._extract_montant_tva(full_text),  # contrôle interne uniquement
        }

    # ------------------------------------------------------------
    def _montant_apres_label(self, text, label_patterns, window=70):
        for label_pattern in label_patterns:
            m = re.search(label_pattern, text, re.IGNORECASE)
            if not m:
                continue
            fenetre = text[m.end(): m.end() + window]
            m2 = MONTANT_RE.search(fenetre)
            if m2:
                brut = m2.group(1).replace(" ", "").replace(",", ".")
                try:
                    return float(brut)
                except ValueError:
                    continue
        return None

    # ------------------------------------------------------------
    def _extract_fournisseur(self, text):
        patterns = [
            r"maroc\s+telecom",
            r"itissalat\s+al[\s-]*maghrib",
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
    def _extract_numero(self, text):
        """Format A: 'N° Facture : NUM'  |  Format B: 'Facture n° NUM du DATE'"""
        patterns = [
            r"n[°'#]?\s*facture\s*:?\s*(\d{10,20})",
            r"facture\s*n[°'#]?\s*:?\s*(\d{10,20})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    # ------------------------------------------------------------
    def _extract_numero_client(self, text):
        patterns = [
            r"n[°'#]?\s*client\s*:?\s*([\d]+(?:[.,][\d]+){1,6})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    # ------------------------------------------------------------
    def _extract_date(self, text):
        """Format A: 'Date Facture : JJ/MM/AAAA'  |  Format B: 'Facture n° NUM du JJ/MM/AAAA'"""
        patterns = [
            r"date\s+facture\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
            r"facture\s*n[°'#]?\s*:?\s*\d{10,20}\s+du\s+(\d{1,2}/\d{1,2}/\d{4})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
        return m.group(1) if m else None

    # ------------------------------------------------------------
    def _extract_periode(self, text):
        """Format B: 'Mois : Juillet 2024'  |  Format A: 'Période facturée :' + 2 dates"""
        m = re.search(r"mois\s*:?\s*([a-zàâäéèêëîïôöùûüç]+\s+\d{4})", text, re.IGNORECASE)
        if m:
            return m.group(1).strip().capitalize()

        m = re.search(r"p[ée]riode\s+factur[ée]e\s*:?", text, re.IGNORECASE)
        if m:
            fenetre = text[m.end(): m.end() + 120]
            dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", fenetre)
            if len(dates) >= 2:
                return f"{dates[0]} - {dates[1]}"
            if len(dates) == 1:
                return dates[0]
        return None

    # ------------------------------------------------------------
    def _extract_montant_ht(self, text):
        labels = [
            r"total\s+dh\s+ht",
            r"montant\s+ht\b",
        ]
        return self._montant_apres_label(text, labels)

    def _extract_montant_tva(self, text):
        labels = [r"montant\s+tva"]
        return self._montant_apres_label(text, labels)

    def _extract_montant_ttc(self, text):
        """
        Format B: 'Montant à payer DH TTC' (priorité — le mot 'payer' évite
                  de confondre avec 'Solde ... Montant DH TTC' plus haut)
        Format A: 'Montant TTC :'
        """
        labels = [
            r"montant\s+\S{1,3}\s*payer\s+dh\s+ttc",
            r"montant\s+ttc\b",
        ]
        return self._montant_apres_label(text, labels)

    # ------------------------------------------------------------
    def validate(self, extracted_data):
        """Contrôle rapide : HT + TVA ≈ TTC (indépendant de validation.py)."""
        ht = extracted_data.get("prix_ht")
        tva = extracted_data.get("montant_tva")
        ttc = extracted_data.get("montant")

        if ht is not None and tva is not None and ttc is not None:
            if abs((ht + tva) - ttc) < 1:
                return True, "Cohérent"
            return False, f"Incohérent : {ht} + {tva} ≠ {ttc}"
        return None, "Données incomplètes"