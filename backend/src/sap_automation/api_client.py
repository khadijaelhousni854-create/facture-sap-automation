import httpx

from sap_automation.models import Facture, LigneFacture, StatutTraitement
from sap_automation.logger import logger

# TODO : confirmer avec le Stagiaire 3 l'adresse/port réels de son API
API_BASE_URL = "http://localhost:8000"

STATUT_A_TRAITER = "extraite"


def _dict_vers_facture(donnees: dict) -> Facture:
    lignes = [
        LigneFacture(
            description=l.get("description", ""),
            quantite=1,  # son schéma LigneFactureCreate n'a pas de champ "quantite"
            prix_unitaire=l.get("montant_ht", 0),
        )
        for l in donnees.get("lignes", [])
    ]

    return Facture(
        facture_id=str(donnees.get("id")),
        fournisseur=donnees.get("fournisseur_nom_extrait", ""),
        numero_facture=donnees.get("numero_facture", ""),
        date_facture=str(donnees.get("date_facture", "")),
        montant_ht=donnees.get("montant_ht", 0),
        montant_tva=donnees.get("montant_tva", 0),
        montant_ttc=donnees.get("montant_ttc", 0),
        lignes=lignes,
    )


async def lister_factures_a_traiter() -> list[Facture]:
    url = f"{API_BASE_URL}/factures/"
    params = {"statut": STATUT_A_TRAITER}
    logger.info(f"Appel API : GET {url} (statut={STATUT_A_TRAITER})")

    async with httpx.AsyncClient() as client:
        try:
            reponse = await client.get(url, params=params, timeout=10)
            reponse.raise_for_status()
            resultats = reponse.json()

            # Sécurité : filtre aussi côté client au cas où le serveur
            # ignorerait encore le paramètre "statut"
            a_traiter = [f for f in resultats if f.get("statut") == STATUT_A_TRAITER]

            logger.info(f"{len(a_traiter)} facture(s) à traiter")
            return [_dict_vers_facture(f) for f in a_traiter]

        except httpx.HTTPError as e:
            logger.error(f"Erreur lors de l'appel à GET /factures/ : {e}")
            return []


async def marquer_en_sap(facture_id: str) -> bool:
    url = f"{API_BASE_URL}/factures/{facture_id}/statut"
    payload = {"statut": "en_sap", "numero_bc": None}

    logger.info(f"Appel API : PUT {url} — passage à en_sap")

    async with httpx.AsyncClient() as client:
        try:
            reponse = await client.put(url, json=payload, timeout=10)
            reponse.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Erreur lors du passage en_sap pour la facture {facture_id} : {e}")
            return False


async def envoyer_statut_final(statut: StatutTraitement) -> bool:
    url = f"{API_BASE_URL}/factures/{statut.facture_id}/statut"
    payload = {
        "statut": statut.statut,
        "numero_bc": statut.bc_numero,
    }

    logger.info(f"Appel API : PUT {url} — payload={payload}")

    async with httpx.AsyncClient() as client:
        try:
            reponse = await client.put(url, json=payload, timeout=10)
            reponse.raise_for_status()
            logger.info(f"Statut final envoyé pour la facture {statut.facture_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Erreur lors de l'envoi du statut final pour la facture {statut.facture_id} : {e}")
            return False