"""
nettoyage.py — nettoyage des données brutes OCR avant validation.

Aligné sur le nouveau schéma partagé (table `factures` créée par
l'équipe). Champs pas encore extraits par l'OCR sont laissés à None :
client, numero_abonnement, numero_appel, periode_debut, periode_fin,
date_limite_paiement, montant_avance_credit, montant_du.
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
    Nettoie une facture brute (sortie OCR) et retourne un dict avec les
    clés du nouveau schéma (table `factures`).

    NB: le montant TTC peut arriver sous la clé "montant" (ancien nom)
    ou "montant_ttc" -> on accepte les deux.
    """
    montant_ttc_source = facture_brute.get("montant_ttc")
    if montant_ttc_source is None:
        montant_ttc_source = facture_brute.get("montant")

    return {
        "fournisseur_nom_extrait": nettoyer_texte(facture_brute.get("nom_fournisseur")),
        "client": nettoyer_texte(facture_brute.get("client")),
        "numero_client": nettoyer_texte(facture_brute.get("numero_client_marsa") or facture_brute.get("numero_client")),
        "numero_facture": nettoyer_numero_facture(facture_brute.get("numero_facture")),
        "type_facture": nettoyer_texte(facture_brute.get("type_facture")),
        "source_fichier": nettoyer_texte(facture_brute.get("source_fichier")),
        "numero_abonnement": nettoyer_texte(facture_brute.get("numero_abonnement")),
        "numero_appel": nettoyer_texte(facture_brute.get("numero_appel")),
        "date_facture": nettoyer_date(facture_brute.get("date_facture")),
        "mois_facture": nettoyer_texte(facture_brute.get("periode_facturation")),
        "periode_debut": nettoyer_date(facture_brute.get("periode_debut")),
        "periode_fin": nettoyer_date(facture_brute.get("periode_fin")),
        "date_limite_paiement": nettoyer_date(facture_brute.get("date_limite_paiement")),
        "montant_ht": nettoyer_montant(facture_brute.get("prix_ht") or facture_brute.get("montant_ht")),
        "montant_tva": nettoyer_montant(facture_brute.get("montant_tva")),
        "montant_ttc": nettoyer_montant(montant_ttc_source),
        "montant_avance_credit": nettoyer_montant(facture_brute.get("montant_avance_credit")),
        "montant_du": nettoyer_montant(facture_brute.get("montant_du")),
    }