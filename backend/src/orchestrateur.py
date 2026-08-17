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
        facture = FactureDB(**donnees_facture, statut="extraite")
        db.add(facture)
        db.commit()
        db.refresh(facture)
        enregistrer_log(db, facture.id, "extraction", "info", "Facture enregistrée en base")

        # 2. Création du BC (simulée pour l'instant)
        facture.statut = "en_sap"
        db.commit()
        numero_bc = creer_bc_simule(donnees_facture)
        enregistrer_log(db, facture.id, "sap", "info", f"BC créé (simulation) : {numero_bc}")

        # 3. Mise à jour finale
        facture.statut = "terminee"
        db.commit()
        return {"facture_id": facture.id, "numero_bc": numero_bc, "statut": "terminee"}

    except Exception as e:
        if facture is not None:
            facture.statut = "erreur"
            db.commit()
            enregistrer_log(db, facture.id, "orchestration", "erreur", str(e))
        else:
            enregistrer_log(db, None, "orchestration", "erreur", str(e))
        raise