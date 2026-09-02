from sqlalchemy.orm import Session
from models.database_models import FactureDB
from services.logger_service import enregistrer_log

from sap_automation.bc_sync import creer_bc


def orchestrer_traitement(donnees_facture: dict, db: Session) -> dict:
    """
    Coordonne : sauvegarde en base -> création BC (via Playwright/SAP) -> mise à jour statut.
    """
    facture = None
    try:
        # 1. Sauvegarde en base
        # NOTE : on garde une copie AVANT de retirer "lignes", car le
        # module Playwright (creer_bc) a besoin des lignes de détail
        # de la facture pour remplir le BC dans SAP.
        donnees_pour_sap = dict(donnees_facture)

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

        # 2. Création du BC (via le vrai module Playwright)
        facture.statut = "en_sap"
        db.commit()

        # On ajoute l'id de la facture aux données envoyées au module
        # Playwright, pour qu'il puisse l'utiliser dans ses logs/objets.
        donnees_pour_sap["id"] = facture.id

        numero_bc = creer_bc(donnees_pour_sap)

        enregistrer_log(
            db,
            etape="sap",
            niveau="info",
            message=f"BC créé : {numero_bc}",
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