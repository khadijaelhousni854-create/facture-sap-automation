# src/ocr/test_multipage.py
"""
Test du pipeline OCR multi-pages sur facture_ADSL_mois_12_2023.pdf,
qui contient 2 factures différentes (Format A page 1, Format B page 2).

But : vérifier que l'OCR + l'extraction donnent de bons résultats sur
CHAQUE page séparément, avec les vraies valeurs comme référence
(lues directement sur le PDF).

Usage :
    python test_multipage.py
    python test_multipage.py --pdf Documents/facture_ADSL_mois_12_2023.pdf --zoom 3
"""

import argparse
import json
import sys
from pathlib import Path

from ocr_engine import OCREngine
from data_extractor import DataExtractor

SEUIL_CONFIANCE_OK = 0.60

# ------------------------------------------------------------
# Valeurs réelles connues, lues directement sur le PDF
# ------------------------------------------------------------
VALEURS_ATTENDUES = {
    0: {  # Page 1 : Format A (Internet Mobile / SODEP DEPA)
        "numero_facture": "0000011774012024",
        "numero_client_marsa": "5.11104.00.00.100006",
        "date_facture": "05/01/2024",
        "prix_ht": 601.20,
        "montant": 721.44,
    },
    1: {  # Page 2 : Format B (ADSL/Fibre / MARSA MAROCFTTH)
        "numero_facture": "0000405866012024",
        "numero_client_marsa": "7.2571863.16",
        "date_facture": "01/01/2024",
        "prix_ht": 2115.00,
        "montant": 2538.01,
    },
}


def comparer_page(index_page, extraits):
    attendu = VALEURS_ATTENDUES.get(index_page)
    if attendu is None:
        print(f"(Pas de valeurs de référence codées pour la page {index_page} — affichage seul)")
        return 0, 0

    print(f"\n--- Comparaison page {index_page} ---")
    nb_corrects = 0
    for champ, valeur_attendue in attendu.items():
        obtenu = extraits.get(champ)
        correct = (obtenu == valeur_attendue)
        if isinstance(valeur_attendue, float) and obtenu is not None:
            correct = abs(obtenu - valeur_attendue) < 0.01
        if correct:
            nb_corrects += 1
        statut = "OK" if correct else "FAUX"
        print(f"  [{statut:4}] {champ:22} attendu={valeur_attendue!r:20} obtenu={obtenu!r}")

    print(f"  Score page {index_page} : {nb_corrects}/{len(attendu)}")
    return nb_corrects, len(attendu)


def main():
    parser = argparse.ArgumentParser(description="Test OCR multi-pages")
    parser.add_argument("--pdf", default="Documents/facture ADSL mois 12 2023.pdf")
    parser.add_argument("--zoom", type=float, default=3.0)
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERREUR : fichier introuvable -> {pdf_path}")
        sys.exit(1)

    print(f"Test sur : {pdf_path} (zoom={args.zoom})")

    engine = OCREngine()
    resultat_ocr = engine.extract_text(pdf_path, zoom=args.zoom)

    if resultat_ocr is None or resultat_ocr["status"] != "success":
        print("ERREUR : l'extraction OCR a échoué.")
        sys.exit(1)

    print(f"\nNombre de pages détectées : {resultat_ocr['nb_pages']}")
    if resultat_ocr["nb_pages"] < 2:
        print("⚠ ATTENTION : ce PDF contient normalement 2 factures (2 pages), "
              "mais une seule a été traitée. Vérifie que ocr_engine.py boucle "
              "bien sur toutes les pages (fix multi-pages).")

    extractor = DataExtractor()
    total_corrects = 0
    total_champs = 0

    for page in resultat_ocr["pages"]:
        index_page = page["page_index"]
        text_data = page["data"]

        confiance_moyenne = (
            sum(item["confidence"] for item in text_data) / len(text_data)
            if text_data else 0.0
        )

        print("\n" + "=" * 70)
        print(f"PAGE {index_page} — {page['elements']} éléments — confiance moyenne : {confiance_moyenne:.2f}")
        print("=" * 70)

        extraits = extractor.extract_fields(text_data)
        print("Champs extraits :")
        print(json.dumps(extraits, indent=2, ensure_ascii=False))

        nb_corrects, nb_total = comparer_page(index_page, extraits)
        total_corrects += nb_corrects
        total_champs += nb_total

        if confiance_moyenne < SEUIL_CONFIANCE_OK:
            print(f"⚠ Confiance basse sur cette page ({confiance_moyenne:.2f} < {SEUIL_CONFIANCE_OK}) "
                  f"— envisager d'augmenter --zoom.")

    print("\n" + "=" * 70)
    print(f"RÉSULTAT GLOBAL : {total_corrects}/{total_champs} champs corrects sur {resultat_ocr['nb_pages']} page(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()