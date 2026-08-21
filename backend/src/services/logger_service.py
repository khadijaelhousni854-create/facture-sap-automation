from datetime import datetime
from sqlalchemy.orm import Session
from models.database_models import LogDB, UtilisateurDB


def obtenir_ou_creer_utilisateur_systeme(db: Session) -> int:
    """
    Retourne l'id de l'utilisateur 'systeme', en le créant s'il n'existe pas encore.
    Utilisé comme utilisateur par défaut pour les logs automatiques.
    """
    utilisateur = db.query(UtilisateurDB).filter_by(psw="systeme").first()
    if not utilisateur:
        utilisateur = UtilisateurDB(psw="systeme")
        db.add(utilisateur)
        db.commit()
        db.refresh(utilisateur)
    return utilisateur.id


def enregistrer_log(
    db: Session,
    etape: str,
    niveau: str,
    message: str,
    action: str | None = None,
    utilisateur_id: int | None = None,
    facture_id: int | None = None,
    commande_id: int | None = None,
    reception_id: int | None = None,
):
    """
    Enregistre une entrée dans la table LOGS.
    Si aucun utilisateur_id n'est fourni, le log est attribué à l'utilisateur
    'systeme' par défaut (ex : actions automatiques de l'orchestrateur).
    """
    if utilisateur_id is None:
        utilisateur_id = obtenir_ou_creer_utilisateur_systeme(db)

    log = LogDB(
        facture_id=facture_id,
        commande_id=commande_id,
        reception_id=reception_id,
        etape=etape,
        niveau=niveau,
        action=action,
        utilisateur_id=utilisateur_id,
        message=message,
        date_creation=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return log