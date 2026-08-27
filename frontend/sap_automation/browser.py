from playwright.async_api import async_playwright


async def lancer_navigateur(headless: bool = False):
    """
    Lance un navigateur Chromium et retourne le navigateur + la page.

    headless=False : le navigateur s'affiche à l'écran (utile pour debug/dev)
    headless=True  : le navigateur tourne en arrière-plan (utile en production)

    TODO plus tard : ajouter ici la connexion/login à SAP Fiori
    une fois qu'on aura les accès (étape 8 du plan).
    """
    playwright = await async_playwright().start()
    navigateur = await playwright.chromium.launch(headless=headless)
    page = await navigateur.new_page()

    return playwright, navigateur, page


async def fermer_navigateur(playwright, navigateur):
    """
    Ferme proprement le navigateur et arrête Playwright.
    À appeler systématiquement à la fin d'un traitement,
    même en cas d'erreur (voir gestion des erreurs, étape 5).
    """
    await navigateur.close()
    await playwright.stop()
