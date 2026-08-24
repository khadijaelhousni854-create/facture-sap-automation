import asyncio

from sap_automation.browser import lancer_navigateur, fermer_navigateur
from sap_automation.bc import creer_bon_de_commande
from sap_automation.reception import creer_reception
from sap_automation.models import Facture, LigneFacture
from sap_automation.retry import retry_async
from sap_automation.logger import logger


async def main():
    facture_test = Facture(
        facture_id="12345",
        fournisseur="IAM",
        numero_facture="F-2026-0456",
        date_facture="2026-08-10",
        montant_ht=1500.00,
        montant_tva=300.00,
        montant_ttc=1800.00,
        lignes=[
            LigneFacture(description="Service télécom", quantite=1, prix_unitaire=1500.00)
        ],
    )

    logger.info("=== Démarrage du traitement de la facture ===")

    playwright, navigateur, page = await lancer_navigateur(headless=False)

    try:
        # Retry automatique : jusqu'à 3 tentatives en cas d'échec, 2s entre chaque
        statut_bc = await retry_async(
            creer_bon_de_commande, page, facture_test,
            max_tentatives=3, delai=2
        )
        print("Résultat BC :", statut_bc)

        if statut_bc.statut == "succes":
            statut_reception = await retry_async(
                creer_reception, page, facture_test, statut_bc.bc_numero,
                max_tentatives=3, delai=2
            )
            print("Résultat réception :", statut_reception)
        else:
            logger.error(f"BC non créé, réception annulée pour la facture {facture_test.facture_id}")

    except Exception as e:
        logger.error(f"Échec définitif du traitement de la facture {facture_test.facture_id} : {e}")

    finally:
        await fermer_navigateur(playwright, navigateur)
        logger.info("=== Fin du traitement ===")


if __name__ == "__main__":
    asyncio.run(main())
