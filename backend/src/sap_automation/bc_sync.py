import asyncio

from sap_automation.browser import lancer_navigateur, fermer_navigateur
from sap_automation.bc import creer_bon_de_commande
from sap_automation.reception import creer_reception
from sap_automation.models import Facture, LigneFacture
from sap_automation.logger import logger


def _dict_vers_facture(donnees: dict) -> Facture:
    lignes_brutes = donnees.get("lignes", []) or []
    lignes = [
        LigneFacture(
            description=l.get("description", ""),
            quantite=1,  # son schéma LigneFactureCreate n'a pas de champ "quantite"
            prix_unitaire=l.get("montant_ht", 0),
        )
        for l in lignes_brutes
    ]

    return Facture(
        facture_id=str(donnees.get("id", "inconnu")),
        fournisseur=donnees.get("fournisseur_nom_extrait", ""),
        numero_facture=donnees.get("numero_facture", ""),
        date_facture=str(donnees.get("date_facture", "")),
        montant_ht=donnees.get("montant_ht", 0),
        montant_tva=donnees.get("montant_tva", 0),
        montant_ttc=donnees.get("montant_ttc", 0),
        lignes=lignes,
    )


async def _creer_bc_et_reception_async(donnees: dict) -> str:
    facture = _dict_vers_facture(donnees)

    playwright, navigateur, page = await lancer_navigateur(headless=False)

    try:
        statut_bc = await creer_bon_de_commande(page, facture)

        if statut_bc.statut != "terminee":
            raise RuntimeError(f"Échec de création du BC : {statut_bc.message}")

        # On enchaîne directement sur la réception (comme prévu dans
        # le flux global : BC puis réception)
        statut_reception = await creer_reception(page, facture, statut_bc.bc_numero)

        if statut_reception.statut != "terminee":
            logger.error(f"BC créé ({statut_bc.bc_numero}) mais réception échouée : {statut_reception.message}")
            # On renvoie quand même le numéro de BC, car il a bien été créé.
            # (Le Stagiaire 3 pourra ajuster ce comportement si besoin.)

        return statut_bc.bc_numero

    finally:
        await fermer_navigateur(playwright, navigateur)


def creer_bc(donnees: dict) -> str:
    logger.info(f"[bc_sync] Démarrage traitement SAP pour la facture {donnees.get('numero_facture')}")
    numero_bc = asyncio.run(_creer_bc_et_reception_async(donnees))
    logger.info(f"[bc_sync] BC obtenu : {numero_bc}")
    return numero_bc

