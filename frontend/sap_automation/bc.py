from sap_automation.models import Facture, StatutTraitement
from sap_automation.logger import logger


async def creer_bon_de_commande(page, facture: Facture) -> StatutTraitement:
    """
    Crée un Bon de Commande dans SAP Fiori à partir des données d'une facture.

    Args:
        page: la page Playwright déjà connectée à SAP Fiori.
        facture: les données de la facture validée (voir models.py).

    Returns:
        StatutTraitement: le résultat de l'opération (succès/échec + numéro BC).

    TODO (étape 8-9) :
    - Naviguer vers l'application Fiori "Créer commande d'achat"
    - Remplir les champs (fournisseur, lignes, montants...)
    - Cliquer sur "Enregistrer"
    - Récupérer le numéro de BC généré
    - Gérer les messages d'erreur SAP spécifiques
    """
    logger.info(f"Début création BC pour la facture {facture.numero_facture} (fournisseur: {facture.fournisseur})")

    try:
        # ---- SIMULATION en attendant le vrai code Playwright/SAP ----
        # TODO : remplacer ce bloc par les vraies actions Playwright
        # (page.goto, page.fill, page.click, etc.)
        print(f"[MOCK] Création du BC pour la facture {facture.numero_facture}...")

        resultat = StatutTraitement(
            facture_id=facture.facture_id,
            statut="succes",
            bc_numero="BC-SIMULE-0001",
            reception_numero=None,
            message="Simulation - à remplacer par le vrai traitement SAP",
        )

        logger.info(f"BC créé avec succès : {resultat.bc_numero} (facture {facture.facture_id})")
        return resultat

    except Exception as e:
        logger.error(f"Échec de création du BC pour la facture {facture.facture_id} : {e}")
        return StatutTraitement(
            facture_id=facture.facture_id,
            statut="erreur_sap",
            bc_numero=None,
            reception_numero=None,
            message=str(e),
        )
