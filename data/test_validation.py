"""
test_validation.py — Test isolé de nettoyage.py + validation.py,
sans dépendre de l'OCR (données construites à la main).

Usage :
    python test_validation.py
"""

import json

from nettoyage import nettoyer_facture
from validation import valider_facture


CAS_DE_TEST = [
    {
        "nom": "Facture propre (déjà bien formatée)",
        "donnees": {
            "nom_fournisseur": "Maroc Telecom",
            "numero_facture": "0000169627082024",
            "numero_client_marsa": "7.2571863.15",
            "date_facture": "2024-08-01",
            "periode_facturation": "Juillet 2024",
            "prix_ht": 1936.84,
            "montant": 2324.20,
            "source_fichier": "facture_telephonie_2.pdf",
        },
        "attendu": "VALIDE",
    },
    {
        "nom": "Facture 'sale' (formats bruts OCR à nettoyer)",
        "donnees": {
            "nom_fournisseur": "  Maroc   Telecom  ",
            "numero_facture": "0000011774012024",
            "numero_client_marsa": "5.11104.00.00.100006",
            "date_facture": "05/01/2024",           # JJ/MM/AAAA -> doit devenir AAAA-MM-JJ
            "periode_facturation": "Décembre 2023",
            "prix_ht": "601,20 DH",                  # virgule + "DH" -> doit devenir 601.2
            "montant": "721,44 DH",
            "source_fichier": "facture_ADSL_mois_12_2023.pdf",
        },
        "attendu": "VALIDE",
    },
    {
        "nom": "Champ obligatoire manquant (numero_client_marsa vide)",
        "donnees": {
            "nom_fournisseur": "Maroc Telecom",
            "numero_facture": "0000012544042024",
            "numero_client_marsa": "",
            "date_facture": "04/04/2024",
            "prix_ht": 165.83,
            "montant": 199.00,
            "source_fichier": "facture_adsl_2.pdf",
        },
        "attendu": "REJETE",
    },
    {
        "nom": "Montant incohérent (montant < prix_ht)",
        "donnees": {
            "nom_fournisseur": "Maroc Telecom",
            "numero_facture": "TEST-INCOHERENT-001",
            "numero_client_marsa": "7.2571863.16",
            "date_facture": "01/04/2024",
            "prix_ht": 900.00,
            "montant": 500.00,
            "source_fichier": "facture_test.pdf",
        },
        "attendu": "REJETE",
    },
    {
        "nom": "Montant négatif",
        "donnees": {
            "nom_fournisseur": "Maroc Telecom",
            "numero_facture": "TEST-NEGATIF-001",
            "numero_client_marsa": "7.2571863.16",
            "date_facture": "01/04/2024",
            "prix_ht": -100.00,
            "montant": 199.00,
            "source_fichier": "facture_test.pdf",
        },
        "attendu": "REJETE",
    },
    {
        "nom": "Numéro de facture avec zéros initiaux (ne doit pas être tronqué)",
        "donnees": {
            "nom_fournisseur": "Maroc Telecom",
            "numero_facture": "0000009661042024",
            "numero_client_marsa": "7.2571863.16",
            "date_facture": "01/04/2024",
            "prix_ht": 1948.33,
            "montant": 2338.00,
            "source_fichier": "facture_test.pdf",
        },
        "attendu": "VALIDE",
    },
]


def executer_tests():
    nb_reussis = 0
    nb_total = len(CAS_DE_TEST)

    for cas in CAS_DE_TEST:
        print("=" * 70)
        print(f"CAS : {cas['nom']}")
        print("=" * 70)

        facture_nettoyee = nettoyer_facture(cas["donnees"])
        print("Après nettoyage :")
        print(json.dumps(facture_nettoyee, indent=2, ensure_ascii=False))

        resultat = valider_facture(facture_nettoyee)
        print("\nRésultat validation :")
        print(json.dumps(resultat, indent=2, ensure_ascii=False))

        statut_obtenu = resultat["statut_propose"]
        ok = statut_obtenu == cas["attendu"]
        if ok:
            nb_reussis += 1

        # Vérification bonus : le numéro de facture garde bien ses zéros initiaux
        num_original = str(cas["donnees"].get("numero_facture", ""))
        num_nettoye = facture_nettoyee.get("numero_facture") or ""
        if num_original and num_original != num_nettoye:
            print(f"\n⚠ ATTENTION : numero_facture modifié par le nettoyage "
                  f"({num_original!r} -> {num_nettoye!r})")

        print(f"\n[{'OK' if ok else 'FAUX'}] attendu={cas['attendu']} obtenu={statut_obtenu}\n")

    print("=" * 70)
    print(f"RÉSULTAT GLOBAL : {nb_reussis}/{nb_total} cas corrects")
    print("=" * 70)


if __name__ == "__main__":
    executer_tests()