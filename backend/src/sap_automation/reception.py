import random

from sap_automation.models import Facture, StatutTraitement
from sap_automation.logger import logger


async def creer_reception(page, facture: Facture, bc_numero: str) -> StatutTraitement:
    """
    Crée la réception dans SAP Fiori, liée à un Bon de Commande existant.

    Args:
        page: la page Playwright déjà connectée à SAP Fiori.
        facture: les données de la facture validée.
        bc_numero: le numéro du BC créé précédemment (via bc.py).

    Returns:
        StatutTraitement avec statut "terminee" ou "erreur".

    TODO (étapes finales, une fois accès SAP disponibles) :
    - Naviguer vers l'application Fiori "Créer réception"
    - Rechercher le BC via bc_numero
    - Confirmer la réception des lignes de commande
    - Récupérer le numéro de réception généré
    - Gérer les erreurs SAP spécifiques (session expirée, timeout, popup...)
    """
    logger.info(f"Début création réception pour le BC {bc_numero} (facture {facture.facture_id})")

    try:
        # ---- SIMULATION en attendant le vrai code Playwright/SAP ----
        reception_numero = f"REC-TEST-{random.randint(10000, 99999)}"
        print(f"[MOCK] Création de la réception pour le BC {bc_numero} → {reception_numero}")

        resultat = StatutTraitement(
            facture_id=facture.facture_id,
            statut="terminee",
            bc_numero=bc_numero,
            reception_numero=reception_numero,
            message="Simulation - à remplacer par le vrai traitement SAP",
        )

        logger.info(f"Réception créée avec succès : {resultat.reception_numero} (BC {bc_numero})")
        return resultat

    except Exception as e:
        logger.error(f"Échec de création de la réception pour le BC {bc_numero} : {e}")
        return StatutTraitement(
            facture_id=facture.facture_id,
            statut="erreur",
            bc_numero=bc_numero,
            reception_numero=None,
            message=str(e),
            type_erreur="inconnue",
        )