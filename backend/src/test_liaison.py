"""
test_liaison.py
-----------
Script de test INDÉPENDANT, qui ne nécessite ni FastAPI ni PostgreSQL.

Objectif : vérifier que le module sap_automation (Playwright) est bien
importable et fonctionnel depuis l'emplacement où il a été placé dans
le projet du Stagiaire 3 (backend/src/sap_automation/), en appelant
directement la fonction creer_bc() avec une facture simulée.

À exécuter depuis backend/src/ :
    python test_liaison.py
"""

from sap_automation.bc_sync import creer_bc


def main():
    print("=== Test de la liaison sap_automation (Option B) ===\n")

    # Facture simulée, au même format que ce que orchestrateur.py
    # enverrait normalement (voir schemas.py -> FactureCreate)
    donnees_test = {
        "id": 1,
        "fournisseur_nom_extrait": "IAM",
        "numero_facture": "F-TEST-001",
        "date_facture": "2026-08-19",
        "montant_ht": 1000,
        "montant_tva": 200,
        "montant_ttc": 1200,
        "lignes": [],
    }

    print(f"Facture de test envoyée : {donnees_test}\n")

    numero_bc = creer_bc(donnees_test)

    print(f"\n=== Résultat ===")
    print(f"Numéro de BC obtenu : {numero_bc}")
    print("\nSi tu vois ce message, la liaison entre ton module Playwright")
    print("et le projet du Stagiaire 3 fonctionne correctement !")


if __name__ == "__main__":
    main()
