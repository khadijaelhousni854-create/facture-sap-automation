from datetime import datetime
from sqlalchemy.orm import Session
from models.database_models import LogDB


def enregistrer_log(
    db: Session,
    etape: str,
    niveau: str,
    message: str,
    action: str | None = None,
    utilisateur: str | None = "systeme",
    facture_id: int | None = None,
    commande_id: int | None = None,
    reception_id: int | None = None,
):
    """
    Enregistre une entrée dans la table LOGS.
    Au moins un des identifiants (facture_id, commande_id, reception_id)
    devrait être fourni pour que le log soit exploitable, mais aucun n'est
    obligatoire (ex: log d'une erreur de connexion en tout début de pipeline).
    """
    log = LogDB(
        facture_id=facture_id,
        commande_id=commande_id,
        reception_id=reception_id,
        etape=etape,
        niveau=niveau,
        action=action,
        utilisateur=utilisateur,
        message=message,
        date_creation=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return log