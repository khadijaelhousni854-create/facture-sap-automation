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
    UtilisateurCreate,
    UtilisateurResponse,
)
from models.database_models import (
    FactureDB,
    FournisseurDB,
    CommandeAchatDB,
    ReceptionDB,
    EntiteDB,
    OCRDataDB,
    LogDB,
    LigneFactureDB,
    FactureRejetDB,
    UtilisateurDB,
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
        commande = db.query(CommandeAchatDB).filter(
            CommandeAchatDB.numero_bc == update.numero_bc
        ).first()
        if not commande:
            commande = CommandeAchatDB(numero_bc=update.numero_bc)
            db.add(commande)
            db.flush()

        reception = ReceptionDB(
            date_documentation=datetime.utcnow().date(),
            commande_id=commande.id,
        )
        db.add(reception)

        commande.facture_id = facture.id

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
# ENTITES + RATTACHER (facture <-> entité, colonne FK directe)
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


@app.put("/factures/{facture_id}/entite/{entite_id}")
def rattacher_facture_entite(facture_id: int, entite_id: int, db: Session = Depends(get_db)):
    """Relation RATTACHER (1,1 - 1,N) : lie une facture à une entité/centre de coûts."""
    facture = db.query(FactureDB).filter(FactureDB.id == facture_id).first()
    entite = db.query(EntiteDB).filter(EntiteDB.id == entite_id).first()
    if not facture or not entite:
        raise HTTPException(status_code=404, detail="Facture ou entité introuvable")

    if facture.entite_id is not None:
        raise HTTPException(status_code=409, detail="Cette facture est déjà rattachée à une entité")

    facture.entite_id = entite_id
    db.commit()
    return {"facture_id": facture_id, "entite_id": entite_id}


# ===================================================================
# UTILISATEURS + rattachement à une entité (association APPARTENIR)
# ===================================================================
@app.post("/utilisateurs/", response_model=UtilisateurResponse)
def creer_utilisateur(utilisateur: UtilisateurCreate, db: Session = Depends(get_db)):
    nouvel_utilisateur = UtilisateurDB(**utilisateur.dict())
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    return nouvel_utilisateur


@app.get("/utilisateurs/", response_model=list[UtilisateurResponse])
def lister_utilisateurs(db: Session = Depends(get_db)):
    return db.query(UtilisateurDB).all()


@app.put("/utilisateurs/{utilisateur_id}/entite/{entite_id}")
def rattacher_utilisateur_entite(utilisateur_id: int, entite_id: int, db: Session = Depends(get_db)):
    """Relation APPARTENIR (0,1 - 1,N) : associe un utilisateur à son entité."""
    utilisateur = db.query(UtilisateurDB).filter(UtilisateurDB.id == utilisateur_id).first()
    entite = db.query(EntiteDB).filter(EntiteDB.id == entite_id).first()
    if not utilisateur or not entite:
        raise HTTPException(status_code=404, detail="Utilisateur ou entité introuvable")
    utilisateur.entite_id = entite_id
    db.commit()
    return {"utilisateur_id": utilisateur_id, "entite_id": entite_id}


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