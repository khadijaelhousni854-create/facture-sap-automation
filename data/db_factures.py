
"""
db_factures.py

Connexion PostgreSQL et pipeline complet :
nettoyage -> validation -> vérification doublon -> insertion.

Ce module assure :
- la connexion à PostgreSQL ;
- la gestion des fournisseurs ;
- la détection des doublons ;
- l'insertion des factures ;
- l'enregistrement des rejets ;
- la journalisation du traitement.
"""

import io
import logging
import sys

import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json

from config import DB_CONFIG
from nettoyage import nettoyer_facture
from validation import (
    valider_facture,
    STATUT_VALIDE,
    STATUT_REJETE,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Évite les problèmes d'encodage dans le terminal Windows.
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
    )


logging.basicConfig(
    filename="traitement_factures.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Connexion PostgreSQL
# ---------------------------------------------------------------------------

def get_connection():
    """
    Ouvre une connexion PostgreSQL à partir de DB_CONFIG.
    """
    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------------------------
# Fournisseur
# ---------------------------------------------------------------------------

def obtenir_ou_creer_fournisseur(nom_fournisseur: str) -> int:
    """
    Retourne l'id du fournisseur existant.

    Si le fournisseur n'existe pas, il est créé dans la table
    `fournisseur`.

    Paramètre
    ---------
    nom_fournisseur : str
        Nom du fournisseur extrait de la facture.

    Retour
    ------
    int
        Identifiant du fournisseur.
    """

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:

                # Recherche du fournisseur existant.
                cur.execute(
                    """
                    SELECT id
                    FROM fournisseur
                    WHERE nom = %s;
                    """,
                    (nom_fournisseur,),
                )

                ligne = cur.fetchone()

                if ligne:
                    return ligne[0]

                # Création du fournisseur.
                cur.execute(
                    """
                    INSERT INTO fournisseur (nom)
                    VALUES (%s)
                    RETURNING id;
                    """,
                    (nom_fournisseur,),
                )

                return cur.fetchone()[0]

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Détection des doublons
# ---------------------------------------------------------------------------

def facture_existe_deja(numero_facture: str) -> bool:
    """
    Vérifie si une facture portant déjà ce numéro existe dans PostgreSQL.

    Retourne :
        True  -> facture déjà présente
        False -> facture absente
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT 1
                FROM factures
                WHERE numero_facture = %s
                LIMIT 1;
                """,
                (numero_facture,),
            )

            return cur.fetchone() is not None

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Insertion facture
# ---------------------------------------------------------------------------

def inserer_facture(facture: dict) -> dict:
    """
    Insère une facture dans la table `factures`.

    Retourne un dictionnaire indiquant :
    - le succès de l'opération ;
    - l'identifiant créé ;
    - ou la raison de l'échec.
    """

    sql = """
        INSERT INTO factures (
            fournisseur_nom_extrait,
            fournisseur_id,
            client,
            numero_client,
            numero_facture,
            type_facture,
            source_fichier,
            numero_abonnement,
            numero_appel,
            date_facture,
            mois_facture,
            periode_debut,
            periode_fin,
            date_limite_paiement,
            montant_ht,
            montant_tva,
            montant_ttc,
            montant_avance_credit,
            montant_du,
            est_duplicata,
            statut,
            erreur_validation,
            entite_id
        )
        VALUES (
            %(fournisseur_nom_extrait)s,
            %(fournisseur_id)s,
            %(client)s,
            %(numero_client)s,
            %(numero_facture)s,
            %(type_facture)s,
            %(source_fichier)s,
            %(numero_abonnement)s,
            %(numero_appel)s,
            %(date_facture)s,
            %(mois_facture)s,
            %(periode_debut)s,
            %(periode_fin)s,
            %(date_limite_paiement)s,
            %(montant_ht)s,
            %(montant_tva)s,
            %(montant_ttc)s,
            %(montant_avance_credit)s,
            %(montant_du)s,
            %(est_duplicata)s,
            %(statut)s,
            %(erreur_validation)s,
            %(entite_id)s
        )
        RETURNING id;
    """

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:

                cur.execute(sql, facture)

                facture_id = cur.fetchone()[0]

                return {
                    "succes": True,
                    "id_facture": facture_id,
                }

    except errors.UniqueViolation:
        return {
            "succes": False,
            "raison": "doublon",
        }

    except Exception as e:
        return {
            "succes": False,
            "raison": "erreur",
            "detail": str(e),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Enregistrement des rejets
# ---------------------------------------------------------------------------

def enregistrer_rejet(
    facture_brute: dict,
    numero_facture,
    fournisseur: str,
    raison: str,
):
    """
    Enregistre une facture rejetée dans la table `facture_rejet`.

    Les données OCR brutes sont conservées dans `donnees_brutes`.
    """

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO facture_rejet (
                        numero_facture,
                        fournisseur,
                        raison,
                        donnees_brutes,
                        date_rejet
                    )
                    VALUES (%s, %s, %s, %s, NOW());
                    """,
                    (
                        numero_facture,
                        fournisseur,
                        raison,
                        Json(facture_brute),
                    ),
                )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def traiter_facture(facture_brute: dict) -> dict:
    """
    Pipeline complet pour une facture brute issue de l'OCR :

        1. Nettoyage
        2. Validation
        3. Vérification du numéro de facture
        4. Détection du doublon
        5. Vérification des champs nécessaires
        6. Gestion du fournisseur
        7. Insertion PostgreSQL
        8. Enregistrement éventuel du rejet
        9. Journalisation

    Paramètre
    ---------
    facture_brute : dict
        Données brutes provenant de l'OCR.

    Retour
    ------
    dict
        Résultat du traitement.
    """

    # -----------------------------------------------------------------------
    # 1. Nettoyage
    # -----------------------------------------------------------------------

    facture = nettoyer_facture(facture_brute)

    numero_facture = facture.get("numero_facture")

    nom_fournisseur = (
        facture.get("fournisseur_nom_extrait")
        or facture.get("nom_fournisseur")
        or "INCONNU"
    )

    # -----------------------------------------------------------------------
    # 2. Validation métier
    # -----------------------------------------------------------------------

    resultat_validation = valider_facture(facture)

    erreurs_validation = resultat_validation.get("erreurs", [])

    # -----------------------------------------------------------------------
    # 3. Numéro de facture obligatoire
    # -----------------------------------------------------------------------

    if not numero_facture:

        logging.warning(
            "Rejet (numero_facture manquant) | source=%s",
            facture.get("source_fichier"),
        )

        erreurs = erreurs_validation or [
            "Champ obligatoire manquant : numero_facture"
        ]

        enregistrer_rejet(
            facture_brute=facture_brute,
            numero_facture=None,
            fournisseur=nom_fournisseur,
            raison=" | ".join(erreurs),
        )

        return {
            "statut": STATUT_REJETE,
            "erreurs": erreurs,
        }

    # -----------------------------------------------------------------------
    # 4. Vérification du doublon
    # -----------------------------------------------------------------------

    if facture_existe_deja(numero_facture):

        logging.info(
            "Doublon détecté | numero_facture=%s",
            numero_facture,
        )

        return {
            "statut": "DOUBLON",
            "numero_facture": numero_facture,
        }

    # -----------------------------------------------------------------------
    # 5. Vérification des champs nécessaires à l'insertion
    # -----------------------------------------------------------------------

    champs_requis_table = [
        "numero_client",
        "date_facture",
        "montant_ht",
        "montant_ttc",
    ]

    champs_manquants = [
        champ
        for champ in champs_requis_table
        if facture.get(champ) is None
    ]

    if champs_manquants:

        logging.warning(
            "Rejet (champs manquants : %s) | numero_facture=%s",
            champs_manquants,
            numero_facture,
        )

        erreurs = list(erreurs_validation)

        erreurs.append(
            f"Champs manquants pour insertion : {champs_manquants}"
        )

        enregistrer_rejet(
            facture_brute=facture_brute,
            numero_facture=numero_facture,
            fournisseur=nom_fournisseur,
            raison=" | ".join(erreurs),
        )

        return {
            "statut": STATUT_REJETE,
            "numero_facture": numero_facture,
            "erreurs": erreurs,
        }

    # -----------------------------------------------------------------------
    # 6. Récupération / création du fournisseur
    # -----------------------------------------------------------------------

    try:

        id_fournisseur = obtenir_ou_creer_fournisseur(
            nom_fournisseur
        )

    except Exception as e:

        logging.error(
            "Erreur fournisseur | nom=%s | %s",
            nom_fournisseur,
            e,
        )

        return {
            "statut": "ERREUR",
            "detail": str(e),
        }

    # -----------------------------------------------------------------------
    # 7. Préparation de la ligne facture
    # -----------------------------------------------------------------------

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

        "date_limite_paiement": facture.get(
            "date_limite_paiement"
        ),

        "montant_ht": facture.get("montant_ht"),
        "montant_tva": facture.get("montant_tva"),
        "montant_ttc": facture.get("montant_ttc"),

        "montant_avance_credit": facture.get(
            "montant_avance_credit"
        ),

        "montant_du": facture.get("montant_du"),

        "est_duplicata": False,

        "statut": resultat_validation.get(
            "statut_propose",
            STATUT_VALIDE,
        ),

        "erreur_validation": (
            " | ".join(erreurs_validation)
            if erreurs_validation
            else None
        ),

        "entite_id": None,
    }

    # -----------------------------------------------------------------------
    # 8. Insertion PostgreSQL
    # -----------------------------------------------------------------------

    resultat_insertion = inserer_facture(ligne)

    # -----------------------------------------------------------------------
    # 9. Gestion du résultat d'insertion
    # -----------------------------------------------------------------------

    if not resultat_insertion["succes"]:

        if resultat_insertion.get("raison") == "doublon":

            logging.info(
                "Doublon détecté à l'insertion | numero_facture=%s",
                numero_facture,
            )

            return {
                "statut": "DOUBLON",
                "numero_facture": numero_facture,
            }

        logging.error(
            "Erreur technique | numero_facture=%s | %s",
            numero_facture,
            resultat_insertion.get("detail"),
        )

        return {
            "statut": "ERREUR",
            "detail": resultat_insertion.get("detail"),
        }

    # -----------------------------------------------------------------------
    # 10. Enregistrement du rejet si validation rejetée
    # -----------------------------------------------------------------------

    if ligne["statut"] == STATUT_REJETE:

        enregistrer_rejet(
            facture_brute=facture_brute,
            numero_facture=numero_facture,
            fournisseur=nom_fournisseur,
            raison=ligne["erreur_validation"] or "",
        )

    # -----------------------------------------------------------------------
    # 11. Journalisation finale
    # -----------------------------------------------------------------------

    logging.info(
        "Facture insérée | numero_facture=%s | statut=%s",
        numero_facture,
        ligne["statut"],
    )

    return {
        "statut": ligne["statut"],
        "id_facture": resultat_insertion["id_facture"],
        "erreurs": erreurs_validation,
    }

