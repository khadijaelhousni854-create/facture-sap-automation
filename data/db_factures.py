"""
db_factures.py — connexion PostgreSQL et pipeline complet :
nettoyage -> validation -> vérification doublon -> insertion.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import logging
import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json

from config import DB_CONFIG
from nettoyage import nettoyer_facture
from validation import valider_facture, STATUT_VALIDE, STATUT_REJETE

logging.basicConfig(
    filename="traitement_factures.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def obtenir_ou_creer_fournisseur(nom_fournisseur: str) -> int:
    """Retourne l'id du fournisseur existant, ou le crée (table `fournisseurs`)."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM fournisseurs WHERE nom = %s;",
                    (nom_fournisseur,),
                )
                ligne = cur.fetchone()
                if ligne:
                    return ligne[0]

                cur.execute(
                    "INSERT INTO fournisseurs (nom) VALUES (%s) RETURNING id;",
                    (nom_fournisseur,),
                )
                return cur.fetchone()[0]
    finally:
        conn.close()


def facture_existe_deja(numero_facture: str) -> bool:
    """Vérifie en base si ce numero_facture existe déjà (détection de doublon)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM factures WHERE numero_facture = %s LIMIT 1;", (numero_facture,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def inserer_facture(facture: dict) -> dict:
    """Insère une ligne dans la table `factures`."""
    sql = """
        INSERT INTO factures (
            fournisseur_nom_extrait, fournisseur_id, client, numero_client,
            numero_facture, type_facture, source_fichier, numero_abonnement,
            numero_appel, date_facture, mois_facture, periode_debut,
            periode_fin, date_limite_paiement, montant_ht, montant_tva,
            montant_ttc, montant_avance_credit, montant_du, est_duplicata,
            statut, erreur_validation, entite_id
        ) VALUES (
            %(fournisseur_nom_extrait)s, %(fournisseur_id)s, %(client)s, %(numero_client)s,
            %(numero_facture)s, %(type_facture)s, %(source_fichier)s, %(numero_abonnement)s,
            %(numero_appel)s, %(date_facture)s, %(mois_facture)s, %(periode_debut)s,
            %(periode_fin)s, %(date_limite_paiement)s, %(montant_ht)s, %(montant_tva)s,
            %(montant_ttc)s, %(montant_avance_credit)s, %(montant_du)s, %(est_duplicata)s,
            %(statut)s, %(erreur_validation)s, %(entite_id)s
        )
        RETURNING id;
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, facture)
                return {"succes": True, "id_facture": cur.fetchone()[0]}
    except errors.UniqueViolation:
        return {"succes": False, "raison": "doublon"}
    except Exception as e:
        return {"succes": False, "raison": "erreur", "detail": str(e)}
    finally:
        conn.close()


def enregistrer_rejet(facture_brute: dict, numero_facture, fournisseur: str, raison: str):
    """Trace le rejet dans la table dédiée `factures_rejets`."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO factures_rejets (numero_facture, fournisseur, raison, donnees_brutes, date_rejet)
                    VALUES (%s, %s, %s, %s, NOW());
                    """,
                    (numero_facture, fournisseur, raison, Json(facture_brute)),
                )
    finally:
        conn.close()


def traiter_facture(facture_brute: dict) -> dict:
    """
    Pipeline complet pour une facture brute (sortie OCR) :
    nettoyage -> validation -> doublon -> insertion.
    """
    facture = nettoyer_facture(facture_brute)
    numero_facture = facture.get("numero_facture")
    nom_fournisseur = facture.get("fournisseur_nom_extrait") or "INCONNU"

    resultat_validation = valider_facture(facture)

    if not numero_facture:
        logging.warning(f"Rejet (numero_facture manquant) | source={facture.get('source_fichier')}")
        erreurs = resultat_validation["erreurs"] or ["Champ obligatoire manquant : numero_facture"]
        enregistrer_rejet(facture_brute, None, nom_fournisseur, " | ".join(erreurs))
        return {"statut": STATUT_REJETE, "erreurs": erreurs}

    # Vérification du doublon AVANT toute insertion
    if facture_existe_deja(numero_facture):
        logging.info(f"Doublon détecté | numero_facture={numero_facture}")
        return {"statut": "DOUBLON", "numero_facture": numero_facture}

    champs_requis_table = ["numero_client", "date_facture", "montant_ht", "montant_ttc"]
    champs_manquants = [c for c in champs_requis_table if facture.get(c) is None]

    if champs_manquants:
        logging.warning(f"Rejet (champs manquants: {champs_manquants}) | numero_facture={numero_facture}")
        erreurs = resultat_validation["erreurs"] + [f"Champs manquants pour insertion : {champs_manquants}"]
        enregistrer_rejet(facture_brute, numero_facture, nom_fournisseur, " | ".join(erreurs))
        return {"statut": STATUT_REJETE, "erreurs": erreurs}

    id_fournisseur = obtenir_ou_creer_fournisseur(nom_fournisseur)

    ligne = {
        "fournisseur_nom_extrait": nom_fournisseur,
        "fournisseur_id": id_fournisseur,
        "client": facture.get("client"),
        "numero_client": facture.get("numero_client"),
        "numero_facture": numero_facture,
        "type_facture": facture.get("type_facture"),
        "source_fichier": facture.get("source_fichier"),
        "numero_abonnement": facture.get("numero_abonnement"),
        "numero_appel": facture.get("numero_appel"),
        "date_facture": facture.get("date_facture"),
        "mois_facture": facture.get("mois_facture"),
        "periode_debut": facture.get("periode_debut"),
        "periode_fin": facture.get("periode_fin"),
        "date_limite_paiement": facture.get("date_limite_paiement"),
        "montant_ht": facture.get("montant_ht"),
        "montant_tva": facture.get("montant_tva"),
        "montant_ttc": facture.get("montant_ttc"),
        "montant_avance_credit": facture.get("montant_avance_credit"),
        "montant_du": facture.get("montant_du"),
        "est_duplicata": False,
        "statut": resultat_validation["statut_propose"],
        "erreur_validation": " | ".join(resultat_validation["erreurs"]) or None,
        "entite_id": None,
    }

    resultat_insertion = inserer_facture(ligne)

    if not resultat_insertion["succes"]:
        if resultat_insertion.get("raison") == "doublon":
            logging.info(f"Doublon détecté à l'insertion | numero_facture={numero_facture}")
            return {"statut": "DOUBLON", "numero_facture": numero_facture}
        logging.error(f"Erreur technique | numero_facture={numero_facture} | {resultat_insertion.get('detail')}")
        return {"statut": "ERREUR", "detail": resultat_insertion.get("detail")}

    if ligne["statut"] == STATUT_REJETE:
        enregistrer_rejet(facture_brute, numero_facture, nom_fournisseur, ligne["erreur_validation"] or "")

    logging.info(f"Facture insérée | numero_facture={numero_facture} | statut={ligne['statut']}")
    return {
        "statut": ligne["statut"],
        "id_facture": resultat_insertion["id_facture"],
        "erreurs": resultat_validation["erreurs"],
    }