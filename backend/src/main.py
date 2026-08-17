from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, init_db

from schemas import (
    FactureCreate,
    FactureResponse,
    StatutUpdate,
    LogResponse,
    FactureRejetCreate,
    FactureRejetResponse,
    FournisseurResponse,
    EntiteResponse,
    OCRDataResponse,
)
from models.database_models import (
    FactureDB,
    FournisseurDB,
    CommandeAchatDB,
    ReceptionDB,
    LierDB,
    ReceptionnerDB,
    EntiteDB,
    RattacherDB,
    PasserDB,
    OCRDataDB,
    LogDB,
    LigneFactureDB,
    FactureRejetDB,
)
from orchestrateur import orchestrer_traitement

app = FastAPI(title="API RPA IAM - Marsa Maroc")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/factures/", response_model=FactureResponse)
def creer_facture(facture: FactureCreate, db: Session = Depends(get_db)):
    donnees = facture.dict(exclude={"lignes"})
    donnees["date_import"] = datetime.utcnow()
    nouvelle = FactureDB(**donnees)
    db.add(nouvelle)
    db.commit()
    db.refresh(nouvelle)

    for ligne in facture.lignes:
        nouvelle_ligne = LigneFactureDB(
            facture_id=nouvelle.id,
            date_import=datetime.utcnow(),
            **ligne.dict(),
        )
        db.add(nouvelle_ligne)
    db.commit()

    return nouvelle


@app.get("/factures/", response_model=list[FactureResponse])
def lister_factures(db: Session = Depends(get_db)):
    return db.query(FactureDB).all()


@app.get("/factures/{facture_id}", response_model=FactureResponse)
def consulter_facture(facture_id: int, db: Session = Depends(get_db)):
    facture = db.query(FactureDB).filter(FactureDB.id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return facture


@app.put("/factures/{facture_id}/statut")
def maj_statut(facture_id: int, update: StatutUpdate, db: Session = Depends(get_db)):
    facture = db.query(FactureDB).filter(FactureDB.id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    facture.statut = update.statut

    if update.numero_bc:
        # 1. Récupère la commande existante par son numéro, ou la crée si absente
        commande = db.query(CommandeAchatDB).filter(
            CommandeAchatDB.numero_bc == update.numero_bc
        ).first()
        if not commande:
            commande = CommandeAchatDB(numero_bc=update.numero_bc)
            db.add(commande)
            db.flush()  # pour obtenir commande.id sans commit complet

        # 2. Crée une réception liée à cette commande
        reception = ReceptionDB(date_documentation=datetime.utcnow().date())
        db.add(reception)
        db.flush()

        db.add(ReceptionnerDB(commande_id=commande.id, reception_id=reception.id))

        # 3. Lie la facture à cette réception (table LIER)
        db.add(LierDB(facture_id=facture.id, reception_id=reception.id))

    db.commit()
    return {"id": facture_id, "statut": update.statut}


# ===================================================================
# FOURNISSEURS — relation ÉMETTRE
# ===================================================================
@app.post("/fournisseurs/", response_model=FournisseurResponse)
def creer_fournisseur(nom: str, db: Session = Depends(get_db)):
    existant = db.query(FournisseurDB).filter(FournisseurDB.nom == nom).first()
    if existant:
        return existant
    fournisseur = FournisseurDB(nom=nom)
    db.add(fournisseur)
    db.commit()
    db.refresh(fournisseur)
    return fournisseur


@app.get("/fournisseurs/", response_model=list[FournisseurResponse])
def lister_fournisseurs(db: Session = Depends(get_db)):
    return db.query(FournisseurDB).all()


@app.put("/factures/{facture_id}/fournisseur/{fournisseur_id}")
def rattacher_fournisseur_facture(facture_id: int, fournisseur_id: int, db: Session = Depends(get_db)):
    """Relation ÉMETTRE : associe une facture à son fournisseur normalisé."""
    facture = db.query(FactureDB).filter(FactureDB.id == facture_id).first()
    fournisseur = db.query(FournisseurDB).filter(FournisseurDB.id == fournisseur_id).first()
    if not facture or not fournisseur:
        raise HTTPException(status_code=404, detail="Facture ou fournisseur introuvable")
    facture.fournisseur_id = fournisseur_id
    db.commit()
    return {"facture_id": facture_id, "fournisseur_id": fournisseur_id}


# ===================================================================
# ENTITES + RATTACHER
# ===================================================================
@app.post("/entites/", response_model=EntiteResponse)
def creer_entite(nom_entite: str, db: Session = Depends(get_db)):
    existante = db.query(EntiteDB).filter(EntiteDB.nom_entite == nom_entite).first()
    if existante:
        return existante
    entite = EntiteDB(nom_entite=nom_entite)
    db.add(entite)
    db.commit()
    db.refresh(entite)
    return entite


@app.get("/entites/", response_model=list[EntiteResponse])
def lister_entites(db: Session = Depends(get_db)):
    return db.query(EntiteDB).all()


@app.put("/commandes/{commande_id}/entite/{entite_id}")
def rattacher_commande_entite(commande_id: int, entite_id: int, db: Session = Depends(get_db)):
    """Relation RATTACHER (N,N) : lie une commande à une entité/centre de coûts."""
    commande = db.query(CommandeAchatDB).filter(CommandeAchatDB.id == commande_id).first()
    entite = db.query(EntiteDB).filter(EntiteDB.id == entite_id).first()
    if not commande or not entite:
        raise HTTPException(status_code=404, detail="Commande ou entité introuvable")

    deja_lie = db.query(RattacherDB).filter_by(commande_id=commande_id, entite_id=entite_id).first()
    if not deja_lie:
        db.add(RattacherDB(commande_id=commande_id, entite_id=entite_id))
        db.commit()
    return {"commande_id": commande_id, "entite_id": entite_id}


# ===================================================================
# PASSER — relation Fournisseur ↔ Commande
# ===================================================================
@app.put("/commandes/{commande_id}/fournisseur/{fournisseur_id}")
def rattacher_commande_fournisseur(commande_id: int, fournisseur_id: int, db: Session = Depends(get_db)):
    """Relation PASSER (1,N - 0,N) : un fournisseur passe une commande."""
    commande = db.query(CommandeAchatDB).filter(CommandeAchatDB.id == commande_id).first()
    fournisseur = db.query(FournisseurDB).filter(FournisseurDB.id == fournisseur_id).first()
    if not commande or not fournisseur:
        raise HTTPException(status_code=404, detail="Commande ou fournisseur introuvable")

    deja_lie = db.query(PasserDB).filter_by(commande_id=commande_id, fournisseur_id=fournisseur_id).first()
    if not deja_lie:
        db.add(PasserDB(commande_id=commande_id, fournisseur_id=fournisseur_id))
        db.commit()
    return {"commande_id": commande_id, "fournisseur_id": fournisseur_id}


# ===================================================================
# OCR_DATA — relation EXTRAIRE (1,1 - 1,1)
# ===================================================================
@app.post("/factures/{facture_id}/ocr", response_model=OCRDataResponse)
def enregistrer_donnees_ocr(facture_id: int, texte_extrait: str, db: Session = Depends(get_db)):
    facture = db.query(FactureDB).filter(FactureDB.id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    existant = db.query(OCRDataDB).filter(OCRDataDB.facture_id == facture_id).first()
    if existant:
        raise HTTPException(status_code=409, detail="Des données OCR existent déjà pour cette facture")

    ocr = OCRDataDB(
        facture_id=facture_id,
        texte_extrait=texte_extrait,
        date_extraction=datetime.utcnow(),
    )
    db.add(ocr)
    db.commit()
    db.refresh(ocr)
    return ocr


@app.post("/orchestrer/")
def lancer_orchestration(facture: FactureCreate, db: Session = Depends(get_db)):
    resultat = orchestrer_traitement(facture.dict(), db)
    return resultat


@app.get("/logs/", response_model=list[LogResponse])
def lire_tous_les_logs(db: Session = Depends(get_db)):
    return db.query(LogDB).order_by(LogDB.date_creation.desc()).all()


@app.get("/logs/{facture_id}", response_model=list[LogResponse])
def lire_logs_facture(facture_id: int, db: Session = Depends(get_db)):
    return (
        db.query(LogDB)
        .filter(LogDB.facture_id == facture_id)
        .order_by(LogDB.date_creation)
        .all()
    )


@app.post("/factures_rejets/", response_model=FactureRejetResponse)
def creer_facture_rejetee(rejet: FactureRejetCreate, db: Session = Depends(get_db)):
    nouveau_rejet = FactureRejetDB(**rejet.dict(), date_rejet=datetime.now())
    db.add(nouveau_rejet)
    db.commit()
    db.refresh(nouveau_rejet)
    return nouveau_rejet