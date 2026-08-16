"""
validation.py — règles métier de validation d'une facture nettoyée.
"""

from config import STATUT_VALIDE, STATUT_REJETE

CHAMPS_OBLIGATOIRES = [
    "nom_fournisseur",
    "numero_facture",
    "numero_client_marsa",
    "date_facture",
    "prix_ht",
    "montant",
]


def valider_facture(facture: dict) -> dict:
    """
    Vérifie les champs obligatoires et la cohérence de base des montants.

    Retourne :
        {"statut_propose": "VALIDE" | "REJETE", "erreurs": [...]}
    """
    erreurs = []

    for champ in CHAMPS_OBLIGATOIRES:
        valeur = facture.get(champ)
        if valeur is None or (isinstance(valeur, str) and valeur.strip() == ""):
            erreurs.append(f"Champ obligatoire manquant : {champ}")

    if erreurs:
        return {"statut_propose": STATUT_REJETE, "erreurs": erreurs}

    prix_ht = float(facture["prix_ht"])
    montant = float(facture["montant"])

    if prix_ht < 0 or montant < 0:
        erreurs.append("Un montant (prix_ht ou montant) est négatif")

    if montant < prix_ht:
        erreurs.append(f"Montant total ({montant}) inférieur au prix HT ({prix_ht})")

    statut_propose = STATUT_REJETE if erreurs else STATUT_VALIDE
    return {"statut_propose": statut_propose, "erreurs": erreurs}