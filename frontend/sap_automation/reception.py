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
        StatutTraitement: le résultat de l'opération (succès/échec + numéro réception).

    TODO (étape 8-9) :
    - Naviguer vers l'application Fiori "Créer réception"
    - Rechercher le BC via bc_numero
    - Confirmer la réception des lignes de commande
    - Récupérer le numéro de réception généré
    - Gérer les messages d'erreur SAP spécifiques
    """
    logger.info(f"Début création réception pour le BC {bc_numero} (facture {facture.facture_id})")

    try:
        # ---- SIMULATION en attendant le vrai code Playwright/SAP ----
        # TODO : remplacer ce bloc par les vraies actions Playwright
        print(f"[MOCK] Création de la réception pour le BC {bc_numero}...")

        resultat = StatutTraitement(
            facture_id=facture.facture_id,
            statut="succes",
            bc_numero=bc_numero,
            reception_numero="REC-SIMULE-0001",
            message="Simulation - à remplacer par le vrai traitement SAP",
        )

        logger.info(f"Réception créée avec succès : {resultat.reception_numero} (BC {bc_numero})")
        return resultat

    except Exception as e:
        logger.error(f"Échec de création de la réception pour le BC {bc_numero} : {e}")
        return StatutTraitement(
            facture_id=facture.facture_id,
            statut="erreur_sap",
            bc_numero=bc_numero,
            reception_numero=None,
            message=str(e),
        )
