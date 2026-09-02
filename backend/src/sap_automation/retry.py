import asyncio
from sap_automation.logger import logger


async def retry_async(fonction, *args, max_tentatives: int = 3, delai: int = 2, **kwargs):
    """
    Exécute une fonction async, et réessaie en cas d'erreur.

    Args:
        fonction: la fonction async à exécuter (ex: creer_bon_de_commande).
        max_tentatives: nombre maximum d'essais avant d'abandonner.
        delai: temps d'attente (en secondes) entre chaque tentative.
        *args, **kwargs: arguments à passer à la fonction.

    Returns:
        Le résultat de la fonction si elle réussit.

    Raises:
        La dernière exception rencontrée, si toutes les tentatives échouent.
    """
    derniere_erreur = None

    for tentative in range(1, max_tentatives + 1):
        try:
            logger.info(f"Tentative {tentative}/{max_tentatives} pour {fonction.__name__}...")
            resultat = await fonction(*args, **kwargs)
            return resultat

        except Exception as e:
            derniere_erreur = e
            logger.warning(f"Échec tentative {tentative}/{max_tentatives} : {e}")

            if tentative < max_tentatives:
                await asyncio.sleep(delai)

    logger.error(f"Toutes les tentatives ont échoué pour {fonction.__name__} : {derniere_erreur}")
    raise derniere_erreur
