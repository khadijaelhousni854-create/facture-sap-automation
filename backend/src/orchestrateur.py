from sqlalchemy.orm import Session
from models.database_models import FactureDB
from services.logger_service import enregistrer_log


def creer_bc_simule(donnees: dict) -> str:
    """
    Version simulée de la création de BC dans SAP.
    À remplacer plus tard par le vrai module Playwright (Stagiaire 4).
    """
    import random
    return f"BC-TEST-{random.randint(10000, 99999)}"


def orchestrer_traitement(donnees_facture: dict, db: Session) -> dict:
    """
    Coordonne : sauvegarde en base -> création BC -> mise à jour statut.
    """
    facture = None
    try:
        # 1. Sauvegarde en base
        donnees_facture.pop("lignes", None)  # évite le crash si "lignes" est présent
        facture = FactureDB(**donnees_facture, statut="extraite")
        db.add(facture)
        db.commit()
        db.refresh(facture)
        enregistrer_log(
            db,
            etape="extraction",
            niveau="info",
            message="Facture enregistrée en base",
            facture_id=facture.id,
        )

        # 2. Création du BC (simulée pour l'instant)
        facture.statut = "en_sap"
        db.commit()
        numero_bc = creer_bc_simule(donnees_facture)
        enregistrer_log(
            db,
            etape="sap",
            niveau="info",
            message=f"BC créé (simulation) : {numero_bc}",
            facture_id=facture.id,
        )

        # 3. Mise à jour finale
        facture.statut = "terminee"
        db.commit()
        return {"facture_id": facture.id, "numero_bc": numero_bc, "statut": "terminee"}

    except Exception as e:
        if facture is not None:
            facture.statut = "erreur"
            db.commit()
            enregistrer_log(
                db,
                etape="orchestration",
                niveau="erreur",
                message=str(e),
                facture_id=facture.id,
            )
        else:
            enregistrer_log(
                db,
                etape="orchestration",
                niveau="erreur",
                message=str(e),
            )
        raise