# src/ocr/test_batch.py
"""
Test en lot sur un dossier de factures (Documents/), traité par petits
groupes pour ne pas surcharger l'exécution (EasyOCR est lent).

Génère un tableau récapitulatif de tous les champs extraits, affiché à
l'écran ET sauvegardé/complété dans un fichier CSV cumulatif
(resultats_extraction.csv), pour que tu puisses comparer manuellement
avec les vraies factures et repérer les erreurs.

Usage (12 factures, par lots de 4) :
    python test_batch.py --debut 0 --nombre 4
    python test_batch.py --debut 4 --nombre 4
    python test_batch.py --debut 8 --nombre 4

Le CSV s'accumule automatiquement entre les 3 exécutions (pas besoin
de le vider entre chaque lot).
"""

import argparse
import csv
from pathlib import Path

from ocr_engine import OCREngine
from data_extractor import DataExtractor

CHAMPS = [
    "fichier", "page", "nom_fournisseur", "numero_facture",
    "numero_client_marsa", "date_facture", "periode_facturation",
    "prix_ht", "montant", "confiance_moyenne",
]

CSV_PATH = Path("resultats_extraction.csv")


def traiter_lot(dossier, debut, nombre, zoom):
    fichiers = sorted(Path(dossier).glob("*.pdf"))
    lot = fichiers[debut: debut + nombre]

    if not lot:
        print(f"Aucun fichier à traiter pour --debut {debut} (total trouvé : {len(fichiers)})")
        return []

    print(f"Traitement de {len(lot)} fichier(s) : {[f.name for f in lot]}\n")

    engine = OCREngine()
    extractor = DataExtractor()
    lignes = []

    for pdf_path in lot:
        print(f"--> {pdf_path.name}")
        resultat_ocr = engine.extract_text(pdf_path, zoom=zoom)

        if resultat_ocr is None or resultat_ocr["status"] != "success":
            lignes.append({c: "" for c in CHAMPS} | {"fichier": pdf_path.name, "page": "ERREUR_OCR"})
            continue

        for page in resultat_ocr["pages"]:
            text_data = page["data"]
            confiance = (
                sum(d["confidence"] for d in text_data) / len(text_data)
                if text_data else 0.0
            )
            extraits = extractor.extract_fields(text_data)

            lignes.append({
                "fichier": pdf_path.name,
                "page": page["page_index"],
                "nom_fournisseur": extraits.get("nom_fournisseur"),
                "numero_facture": extraits.get("numero_facture"),
                "numero_client_marsa": extraits.get("numero_client_marsa"),
                "date_facture": extraits.get("date_facture"),
                "periode_facturation": extraits.get("periode_facturation"),
                "prix_ht": extraits.get("prix_ht"),
                "montant": extraits.get("montant"),
                "confiance_moyenne": round(confiance, 2),
            })

    return lignes


def afficher_tableau(lignes):
    print("\n" + "=" * 130)
    entete = f"{'fichier':<30} {'pg':<3} {'fournisseur':<14} {'num_facture':<18} {'num_client':<20} {'date':<11} {'HT':<9} {'TTC':<9} {'conf':<5}"
    print(entete)
    print("-" * 130)
    for l in lignes:
        print(
            f"{str(l.get('fichier',''))[:30]:<30} "
            f"{str(l.get('page','')):<3} "
            f"{str(l.get('nom_fournisseur',''))[:14]:<14} "
            f"{str(l.get('numero_facture','')):<18} "
            f"{str(l.get('numero_client_marsa','')):<20} "
            f"{str(l.get('date_facture','')):<11} "
            f"{str(l.get('prix_ht','')):<9} "
            f"{str(l.get('montant','')):<9} "
            f"{str(l.get('confiance_moyenne','')):<5}"
        )
    print("=" * 130)


def sauvegarder_csv(lignes):
    fichier_existe_deja = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CHAMPS)
        if not fichier_existe_deja:
            writer.writeheader()
        for l in lignes:
            writer.writerow(l)
    print(f"\nRésultats ajoutés à : {CSV_PATH.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Test en lot sur les factures")
    parser.add_argument("--dossier", default="Documents")
    parser.add_argument("--debut", type=int, default=0, help="Index du 1er fichier du lot (0, 4, 8...)")
    parser.add_argument("--nombre", type=int, default=4, help="Nombre de fichiers dans ce lot")
    parser.add_argument("--zoom", type=float, default=3.0)
    args = parser.parse_args()

    lignes = traiter_lot(args.dossier, args.debut, args.nombre, args.zoom)
    if lignes:
        afficher_tableau(lignes)
        sauvegarder_csv(lignes)


if __name__ == "__main__":
    main()