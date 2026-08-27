# test_pipeline_complet.py
"""
Test du pipeline complet, de bout en bout :
OCR -> extraction -> nettoyage -> validation -> insertion PostgreSQL (Neon).

À placer à la racine du projet (facture-sap-automation/), car il importe
depuis ocr/ ET data/.

Usage :
    python test_pipeline_complet.py Documents/facture_telephonie_2.pdf
    python test_pipeline_complet.py Documents/facture_telephonie_2.pdf --zoom 4
    python test_pipeline_complet.py Documents/                          # tout le dossier
"""

import argparse
import json
import sys
from pathlib import Path

# Permet d'importer depuis les 2 sous-dossiers du projet
sys.path.append(str(Path(__file__).resolve().parent / "ocr"))
sys.path.append(str(Path(__file__).resolve().parent / "data"))

from ocr.ocr_engine import OCREngine
from ocr.data_extractor import DataExtractor
from data.db_factures import traiter_facture, get_connection


def tester_connexion():
    """Vérifie que la connexion à Neon fonctionne avant de lancer quoi que ce soit."""
    print("=" * 70)
    print("ÉTAPE 0 — Test de connexion à la base")
    print("=" * 70)
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [t[0] for t in cur.fetchall()]
        conn.close()
        print(f"Connexion réussie ✅ — tables trouvées : {tables}\n")
        return True
    except Exception as e:
        print(f"Connexion échouée ❌\n{e}\n")
        return False


def traiter_un_pdf(pdf_path, engine, extractor, zoom):
    """Exécute le pipeline complet sur un seul PDF (toutes ses pages)."""
    print("=" * 70)
    print(f"FICHIER : {pdf_path.name}")
    print("=" * 70)

    resultat_ocr = engine.extract_text(pdf_path, zoom=zoom)
    if resultat_ocr is None or resultat_ocr["status"] != "success":
        print("❌ Échec OCR sur ce fichier, on passe au suivant.\n")
        return

    for page in resultat_ocr["pages"]:
        index_page = page["page_index"]
        text_data = page["data"]
        confiance = (
            sum(d["confidence"] for d in text_data) / len(text_data)
            if text_data else 0.0
        )

        print(f"\n--- Page {index_page} (confiance moyenne : {confiance:.2f}) ---")

        # 1. Extraction des champs
        donnees_brutes = extractor.extract_fields(text_data)
        donnees_brutes["source_fichier"] = pdf_path.name

        print("Champs extraits (OCR) :")
        print(json.dumps(donnees_brutes, indent=2, ensure_ascii=False))

        # 2. Pipeline complet (nettoyage -> validation -> doublon -> insertion)
        resultat = traiter_facture(donnees_brutes)

        print("\nRésultat du pipeline (nettoyage + validation + DB) :")
        print(json.dumps(resultat, indent=2, ensure_ascii=False, default=str))
        print()


def main():
    parser = argparse.ArgumentParser(description="Test du pipeline complet OCR -> DB")
    parser.add_argument("chemin", help="Chemin vers un PDF, ou vers un dossier de PDF")
    parser.add_argument("--zoom", type=float, default=3.0)
    args = parser.parse_args()

    if not tester_connexion():
        print("Arrêt : corrige la connexion avant de continuer.")
        sys.exit(1)

    chemin = Path(args.chemin)
    if chemin.is_dir():
        fichiers = sorted(chemin.glob("*.pdf"))
    elif chemin.is_file():
        fichiers = [chemin]
    else:
        print(f"ERREUR : chemin introuvable -> {chemin}")
        sys.exit(1)

    if not fichiers:
        print("Aucun fichier PDF trouvé.")
        sys.exit(1)

    print(f"Traitement de {len(fichiers)} fichier(s)...\n")

    engine = OCREngine()
    extractor = DataExtractor()

    for pdf_path in fichiers:
        traiter_un_pdf(pdf_path, engine, extractor, args.zoom)

    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    main()