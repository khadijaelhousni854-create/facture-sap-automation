# src/ocr/data_extractor.py
"""
data_extractor.py — Extraction des champs métier à partir du texte OCR.

Sortie alignée sur les clés attendues par nettoyage.nettoyer_facture() :
    nom_fournisseur, numero_facture, numero_client_marsa, date_facture,
    periode_facturation, type_facture, prix_ht, montant

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

    _CAR_NUM = r"[0-9oOØø]"

    def extract_fields(self, text_data):
        full_text = " ".join(item["text"] for item in text_data)

        return {
            "nom_fournisseur": self._extract_fournisseur(full_text),
            "numero_facture": self._extract_numero(full_text),
            "numero_client_marsa": self._extract_numero_client(full_text),
            "date_facture": self._extract_date(full_text),
            "periode_facturation": self._extract_periode(full_text),
            "type_facture": self._extract_type_facture(full_text),
            "prix_ht": self._extract_montant_ht(full_text),
            "montant": self._extract_montant_ttc(full_text),      # clé "montant" (TTC)
            "montant_tva": self._extract_montant_tva(full_text),  # contrôle interne uniquement
        }

    # ------------------------------------------------------------
    # OUTIL COMMUN : chercher le 1er montant qui suit un label donné
    # ------------------------------------------------------------
    def _montant_apres_label(self, text, label_patterns, window=40):
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
    # FOURNISSEUR
    # ------------------------------------------------------------
    def _extract_fournisseur(self, text):
        """Reconnaît le nom du fournisseur parmi une liste de motifs connus."""
        patterns = [
            r"maroc\s+telecom",
            r"itissalat\s+al[\s-]*maghrib",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(0).upper()
        # Toutes les factures traitées (pilote IAM) proviennent de Maroc
        # Telecom ; le nom n'apparaît pas toujours en texte lisible
        # (parfois juste en logo/image), donc on retombe sur cette valeur
        # par défaut plutôt que de risquer de capturer le nom du CLIENT
        # (ex: "SODEP DEPA") par erreur.
        return "MAROC TELECOM"

    # ------------------------------------------------------------
    # TYPE DE FACTURE (catégorie de service)
    # ------------------------------------------------------------
    def _extract_type_facture(self, text):
        """
        Catégorie de service, détectée par mots-clés caractéristiques.
        Catégories connues : INTERNET_MOBILE, VPN, TELEPHONIE, ADSL_FIBRE.
        """
        if re.search(r"abonnement\s+internet\s+mobile", text, re.IGNORECASE):
            return "INTERNET_MOBILE"
        if re.search(r"\bvpn\b", text, re.IGNORECASE):
            return "VPN"
        if re.search(r"lign?e?\s+sp[ée]cialis[ée]e|acc[eè]s\s+primaire|\bpri\b|t[ée]l[ée]phonie", text, re.IGNORECASE):
            return "TELEPHONIE"
        if re.search(r"adsl|fibre\s+optique|menara", text, re.IGNORECASE):
            return "ADSL_FIBRE"
        return "AUTRE"

    # ------------------------------------------------------------
    # NUMÉRO DE FACTURE
    # ------------------------------------------------------------
    def _normaliser_numero(self, brut):
        """Retire les espaces parasites et convertit les lettres qui
        représentent en réalité un zéro mal reconnu par l'OCR."""
        texte = brut.replace(" ", "")
        for car in ("O", "o", "Ø", "ø"):
            texte = texte.replace(car, "0")
        return texte

    def _extract_numero(self, text):
        """
        Extrait le numéro de facture (16 chiffres en général), robuste :
          - au symbole séparateur mal lu (°, ', º, absent...)
          - aux zéros du début confondus avec la lettre "O" par l'OCR
          - aux espaces parasites insérés dans le numéro

        Stratégie :
          1) Ancré sur "facture" : le plus fiable.
          2) Repli (n'importe où dans le texte) : accepté UNIQUEMENT si
             le numéro passe le test de plausibilité (6 derniers
             chiffres = mois/année crédible).
        """
        candidats_ancres = [
            self._normaliser_numero(m.group(1))
            for m in re.finditer(
                rf"facture\D{{0,15}}({self._CAR_NUM}[{self._CAR_NUM} ]{{8,25}}{self._CAR_NUM})",
                text, re.IGNORECASE,
            )
        ]
        candidats_repli = [
            self._normaliser_numero(m.group(1))
            for m in re.finditer(
                rf"({self._CAR_NUM}[{self._CAR_NUM} ]{{12,24}}{self._CAR_NUM})",
                text,
            )
        ]

        for num in candidats_ancres + candidats_repli:
            if self._numero_facture_plausible(num):
                return num

        if candidats_ancres:
            return candidats_ancres[0]

        return None

    def _numero_facture_plausible(self, num):
        """
        Vérifie que le numéro a une longueur plausible (14-18 chiffres)
        et que ses 6 derniers chiffres forment un couple mois/année
        crédible (MMAAAA, mois 01-12, année 2015-2035).
        """
        if not (14 <= len(num) <= 18):
            return False
        mois, annee = num[-6:-4], num[-4:]
        try:
            m, a = int(mois), int(annee)
        except ValueError:
            return False
        return 1 <= m <= 12 and 2015 <= a <= 2035

    # ------------------------------------------------------------
    # NUMÉRO DE CLIENT MARSA MAROC
    # ------------------------------------------------------------
    def _extract_numero_client(self, text):
        """
        Numéro de client : suite de groupes de chiffres séparés par des
        points, précédée de "N° client" (le "°" est parfois lu comme une
        apostrophe ou un "º" par l'OCR).
        Exemples réels : "7.2571863.15", "5.11104.00.00.100006",
        "7.1186404.00.00.100438".
        """
        patterns = [
            r"n[°'º#]?\s*client\s*:?\s*([\d]+(?:[.,][\d]+){1,6})",
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
        """
        Format A : "Date Facture : JJ/MM/AAAA"
        Format B : "Facture n° NUM du JJ/MM/AAAA"
        """
        patterns = [
            r"date\s+facture\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
            r"facture\D{0,25}\d{10,20}\s+du\s+(\d{1,2}/\d{1,2}/\d{4})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
        return m.group(1) if m else None

    # ------------------------------------------------------------
    # PÉRIODE DE FACTURATION
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
    # MONTANTS
    # ------------------------------------------------------------
    def _extract_montant_ht(self, text):
        """
        Format B : "Total DH HT" (le mot "Total" évite de confondre avec
                   l'en-tête de colonne "Montant DH HT")
        Format A : "Montant HT :"
        """
        labels = [
            r"total\s+dh\s+ht",
            r"montant\s+ht\b",
        ]
        return self._montant_apres_label(text, labels)

    def _extract_montant_tva(self, text):
        """Champ de contrôle interne uniquement (pas stocké en base)."""
        labels = [r"montant\s+tva"]
        return self._montant_apres_label(text, labels)

    def _extract_montant_ttc(self, text):
        """
        Format B : "Montant à payer DH TTC" en priorité (le mot "payer"
                   évite de confondre avec "Solde ... Montant DH TTC"
                   qui apparaît plus haut dans le texte de ce format)
        Format A : "Montant TTC :"
        """
        labels = [
            r"montant\s+\S{1,3}\s*payer\s+dh\s+ttc",
            r"montant\s+ttc\b",
        ]
        return self._montant_apres_label(text, labels)

    # ------------------------------------------------------------
    # VALIDATION INTERNE (contrôle rapide, indépendant de validation.py)
    # ------------------------------------------------------------
    def validate(self, extracted_data):
        """
        Contrôle rapide de cohérence HT + TVA ≈ TTC, réalisé directement
        après l'extraction OCR (avant même le pipeline de validation.py).
        """
        ht = extracted_data.get("prix_ht")
        tva = extracted_data.get("montant_tva")
        ttc = extracted_data.get("montant")

        if ht is not None and tva is not None and ttc is not None:
            if abs((ht + tva) - ttc) < 1:
                return True, "Cohérent"
            return False, f"Incohérent : {ht} + {tva} ≠ {ttc}"

        return None, "Données incomplètes"