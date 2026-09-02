import asyncio

from sap_automation.browser import lancer_navigateur, fermer_navigateur
from sap_automation.bc import creer_bon_de_commande
from sap_automation.reception import creer_reception
from sap_automation.retry import retry_async
from sap_automation.logger import logger
from sap_automation.api_client import (
    lister_factures_a_traiter,
    marquer_en_sap,
    envoyer_statut_final,
)

# Intervalle entre deux vérifications (en secondes)
INTERVALLE_POLLING = 10


async def traiter_facture(facture):
    """Traite une facture unique : BC + réception + renvoi du statut."""
    logger.info(f"=== Prise en charge de la facture {facture.facture_id} ===")

    # a. Signale que le traitement commence
    await marquer_en_sap(facture.facture_id)

    playwright, navigateur, page = await lancer_navigateur(headless=False)
    statut_final = None

    try:
        # b. Création du BC
        statut_bc = await retry_async(
            creer_bon_de_commande, page, facture,
            max_tentatives=3, delai=2
        )

        if statut_bc.statut != "terminee":
            logger.error(f"BC non créé pour la facture {facture.facture_id}, réception annulée.")
            statut_final = statut_bc
        else:
            # c. Création de la réception
            statut_final = await retry_async(
                creer_reception, page, facture, statut_bc.bc_numero,
                max_tentatives=3, delai=2
            )

    except Exception as e:
        logger.error(f"Échec définitif du traitement de la facture {facture.facture_id} : {e}")
        statut_final = None

    finally:
        await fermer_navigateur(playwright, navigateur)

    # d. Renvoi du résultat final
    if statut_final is not None:
        await envoyer_statut_final(statut_final)
    else:
        logger.error(f"Aucun statut à renvoyer pour la facture {facture.facture_id}.")


async def boucle_polling():
    """Boucle infinie : vérifie régulièrement les nouvelles factures à traiter."""
    logger.info("=== Démarrage de la boucle de polling ===")

    while True:
        factures = await lister_factures_a_traiter()

        for facture in factures:
            await traiter_facture(facture)

        await asyncio.sleep(INTERVALLE_POLLING)


if __name__ == "__main__":
    try:
        asyncio.run(boucle_polling())
    except KeyboardInterrupt:
        logger.info("Arrêt manuel du module (Ctrl+C).")