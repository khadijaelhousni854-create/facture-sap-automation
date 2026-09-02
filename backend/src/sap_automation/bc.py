import random

from sap_automation.models import Facture, StatutTraitement
from sap_automation.logger import logger


async def creer_bon_de_commande(page, facture: Facture) -> StatutTraitement:
    """
    Crée un Bon de Commande dans SAP Fiori à partir des données d'une facture.

    Args:
        page: la page Playwright déjà connectée à SAP Fiori.
        facture: les données de la facture validée.

    Returns:
        StatutTraitement avec statut "terminee" ou "erreur".

    TODO (étapes finales, une fois accès SAP disponibles) :
    - Naviguer vers l'application Fiori "Créer commande d'achat"
    - Remplir les champs (fournisseur, lignes, montants...)
    - Cliquer sur "Enregistrer"
    - Récupérer le numéro de BC généré par SAP
    - Détecter et distinguer les erreurs SAP :
        * session expirée
        * formulaire rejeté
        * temps de chargement trop long (timeout)
        * popup inattendue
    """
    logger.info(f"Début création BC pour la facture {facture.numero_facture} (fournisseur: {facture.fournisseur})")

    try:
        # ---- SIMULATION en attendant le vrai code Playwright/SAP ----
        # Équivalent à la fonction creer_bc_simule() mentionnée par le Stagiaire 3.
        bc_numero = f"BC-TEST-{random.randint(10000, 99999)}"
        print(f"[MOCK] Création du BC pour la facture {facture.numero_facture} → {bc_numero}")

        resultat = StatutTraitement(
            facture_id=facture.facture_id,
            statut="terminee",
            bc_numero=bc_numero,
            reception_numero=None,
            message="Simulation - à remplacer par le vrai traitement SAP",
        )

        logger.info(f"BC créé avec succès : {resultat.bc_numero} (facture {facture.facture_id})")
        return resultat

    except Exception as e:
        logger.error(f"Échec de création du BC pour la facture {facture.facture_id} : {e}")
        return StatutTraitement(
            facture_id=facture.facture_id,
            statut="erreur",
            bc_numero=None,
            reception_numero=None,
            message=str(e),
            type_erreur="inconnue",   # TODO : préciser selon l'erreur réelle une fois SAP branché
        )