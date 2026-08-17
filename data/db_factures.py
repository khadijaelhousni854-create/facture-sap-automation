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

from config import DB_CONFIG, STATUT_DOUBLON
from nettoyage import nettoyer_facture
from validation import valider_facture

# --- Journalisation dans un fichier log (historique / reporting) ---
logging.basicConfig(
    filename="traitement_factures.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def obtenir_ou_creer_fournisseur(nom_fournisseur: str) -> int:
    """Retourne l'id_fournisseur existant, ou crée le fournisseur s'il n'existe pas."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_fournisseur FROM fournisseur WHERE nom_fournisseur = %s;",
                    (nom_fournisseur,),
                )
                ligne = cur.fetchone()
                if ligne:
                    return ligne[0]

                cur.execute(
                    "INSERT INTO fournisseur (nom_fournisseur) VALUES (%s) RETURNING id_fournisseur;",
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
    """Insère une ligne dans la table factures."""
    sql = """
        INSERT INTO factures (
            id_fournisseur, numero_facture, numero_client_marsa, date_facture,
            periode_facturation, prix_ht, montant, statut, erreur, source_fichier
        ) VALUES (
            %(id_fournisseur)s, %(numero_facture)s, %(numero_client_marsa)s, %(date_facture)s,
            %(periode_facturation)s, %(prix_ht)s, %(montant)s, %(statut)s, %(erreur)s, %(source_fichier)s
        )
        RETURNING id_facture;
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


def traiter_facture(facture_brute: dict) -> dict:
    """
    Pipeline complet pour une facture brute (sortie OCR) :
    nettoyage -> validation -> doublon -> insertion.
    """
    facture = nettoyer_facture(facture_brute)
    numero_facture = facture.get("numero_facture")
    nom_fournisseur = facture.get("nom_fournisseur") or "INCONNU"

    resultat_validation = valider_facture(facture)

    # --- Vérifie TOUS les champs obligatoires avant de tenter l'insertion ---
    # (pas seulement numero_facture, car "numero_client_marsa", "date_facture",
    #  "prix_ht" et "montant" sont aussi NOT NULL dans la table)
    if resultat_validation["statut_propose"] != "VALIDE" and not numero_facture:
        # Cas le plus grave : même le numero_facture manque, on ne peut rien tracer
        logging.warning(f"Rejet (numero_facture manquant) | source={facture.get('source_fichier')}")
        return {"statut": "REJETE", "erreurs": resultat_validation["erreurs"]}

    if not numero_facture:
        logging.warning(f"Rejet (numero_facture manquant) | source={facture.get('source_fichier')}")
        return {"statut": "REJETE", "erreurs": ["Champ obligatoire manquant : numero_facture"]}

    # Vérification du doublon AVANT toute insertion
    if facture_existe_deja(numero_facture):
        logging.info(f"Doublon détecté | numero_facture={numero_facture}")
        return {"statut": STATUT_DOUBLON, "numero_facture": numero_facture}

    # --- Si des champs NOT NULL manquent (autres que numero_facture),
    #     on ne peut pas insérer -> on journalise le rejet sans toucher la base ---
    champs_requis_table = ["numero_client_marsa", "date_facture", "prix_ht", "montant"]
    champs_manquants = [c for c in champs_requis_table if facture.get(c) is None]

    if champs_manquants:
        logging.warning(f"Rejet (champs manquants: {champs_manquants}) | numero_facture={numero_facture}")
        return {
            "statut": "REJETE",
            "erreurs": resultat_validation["erreurs"] + [f"Champs manquants pour insertion : {champs_manquants}"],
        }

    id_fournisseur = obtenir_ou_creer_fournisseur(nom_fournisseur)

    ligne = {
        "id_fournisseur": id_fournisseur,
        "numero_facture": numero_facture,
        "numero_client_marsa": facture.get("numero_client_marsa"),
        "date_facture": facture.get("date_facture"),
        "periode_facturation": facture.get("periode_facturation"),
        "prix_ht": facture.get("prix_ht"),
        "montant": facture.get("montant"),
        "statut": resultat_validation["statut_propose"],
        "erreur": " | ".join(resultat_validation["erreurs"]) or None,
        "source_fichier": facture.get("source_fichier"),
    }

    resultat_insertion = inserer_facture(ligne)

    if not resultat_insertion["succes"]:
        if resultat_insertion.get("raison") == "doublon":
            logging.info(f"Doublon détecté à l'insertion | numero_facture={numero_facture}")
            return {"statut": STATUT_DOUBLON, "numero_facture": numero_facture}
        logging.error(f"Erreur technique | numero_facture={numero_facture} | {resultat_insertion.get('detail')}")
        return {"statut": "ERREUR", "detail": resultat_insertion.get("detail")}

    logging.info(f"Facture insérée | numero_facture={numero_facture} | statut={ligne['statut']}")
    return {
        "statut": ligne["statut"],
        "id_facture": resultat_insertion["id_facture"],
        "erreurs": resultat_validation["erreurs"],
    }
