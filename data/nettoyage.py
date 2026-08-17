"""
nettoyage.py — nettoyage des données brutes OCR avant validation.
"""

import re
from datetime import datetime

FORMATS_DATE_ACCEPTES = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]


def nettoyer_date(valeur) -> str | None:
    """Convertit une date, quel que soit son format, vers AAAA-MM-JJ."""
    if valeur is None:
        return None
    if hasattr(valeur, "strftime"):
        return valeur.strftime("%Y-%m-%d")
    texte = str(valeur).strip()
    if not texte:
        return None
    for fmt in FORMATS_DATE_ACCEPTES:
        try:
            return datetime.strptime(texte, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def nettoyer_montant(valeur) -> float | None:
    """Nettoie un montant : supprime DH/espaces, virgule -> point, arrondi 2 décimales."""
    if valeur is None:
        return None
    if isinstance(valeur, (int, float)):
        return round(float(valeur), 2)
    texte = str(valeur).strip()
    if not texte:
        return None
    texte = re.sub(r"(?i)\bdh\b", "", texte)
    texte = texte.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    texte = re.sub(r"[^0-9.\-]", "", texte)
    if texte in ("", "-", "."):
        return None
    try:
        return round(float(texte), 2)
    except ValueError:
        return None


def nettoyer_numero_facture(valeur) -> str | None:
    """Nettoie le numéro de facture SANS le convertir en nombre (garde les zéros initiaux)."""
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte if texte else None


def nettoyer_texte(valeur) -> str | None:
    """Nettoyage générique : supprime les espaces superflus."""
    if valeur is None:
        return None
    texte = " ".join(str(valeur).split())
    return texte if texte else None


def nettoyer_facture(facture_brute: dict) -> dict:
    """
    Nettoie une facture brute (sortie OCR) et retourne un nouveau dict
    avec les clés attendues par la base :
    nom_fournisseur, numero_facture, numero_client_marsa, date_facture,
    periode_facturation, prix_ht, montant, source_fichier.

    NB: le montant TTC peut arriver sous la clé "montant" (déjà renommé
    par l'OCR) ou "montant_ttc" (nom brut) -> on accepte les deux,
    priorité à "montant" s'il est présent.
    """
    montant_source = facture_brute.get("montant")
    if montant_source is None:
        montant_source = facture_brute.get("montant_ttc")

    return {
        "nom_fournisseur": nettoyer_texte(facture_brute.get("nom_fournisseur")),
        "numero_facture": nettoyer_numero_facture(facture_brute.get("numero_facture")),
        "numero_client_marsa": nettoyer_texte(facture_brute.get("numero_client_marsa")),
        "date_facture": nettoyer_date(facture_brute.get("date_facture")),
        "periode_facturation": nettoyer_texte(facture_brute.get("periode_facturation")),
        "prix_ht": nettoyer_montant(facture_brute.get("prix_ht")),
        "montant": nettoyer_montant(montant_source),
        "source_fichier": nettoyer_texte(facture_brute.get("source_fichier")),
    }