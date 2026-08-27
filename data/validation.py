"""
validation.py — règles métier de validation d'une facture nettoyée.
"""

STATUT_VALIDE = "VALIDE"
STATUT_REJETE = "REJETE"

CHAMPS_OBLIGATOIRES = [
    "fournisseur_nom_extrait",
    "numero_facture",
    "numero_client",
    "date_facture",
    "montant_ht",
    "montant_ttc",
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

    montant_ht = float(facture["montant_ht"])
    montant_ttc = float(facture["montant_ttc"])

    if montant_ht < 0 or montant_ttc < 0:
        erreurs.append("Un montant (montant_ht ou montant_ttc) est négatif")

    if montant_ttc < montant_ht:
        erreurs.append(f"Montant TTC ({montant_ttc}) inférieur au montant HT ({montant_ht})")

    statut_propose = STATUT_REJETE if erreurs else STATUT_VALIDE
    return {"statut_propose": statut_propose, "erreurs": erreurs}