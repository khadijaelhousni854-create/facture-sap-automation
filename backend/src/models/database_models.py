from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


# ===================================================================
# UTILISATEURS
# ===================================================================
class UtilisateurDB(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    psw = Column(String(255), nullable=False)

    logs = relationship("LogDB", back_populates="utilisateur_rel")


# ===================================================================
# FOURNISSEURS
# ===================================================================
class FournisseurDB(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(150), unique=True, nullable=False)

    factures = relationship("FactureDB", back_populates="fournisseur_rel")


# ===================================================================
# FACTURES
# ===================================================================
class FactureDB(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, autoincrement=True)

    fournisseur_nom_extrait = Column(String(150))
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)

    client = Column(String(150))
    numero_client = Column(String(50))
    numero_facture = Column(String(50), unique=True)
    type_facture = Column(String(30))
    source_fichier = Column(String(255))
    date_import = Column(DateTime)
    numero_abonnement = Column(String(50))
    numero_appel = Column(String(30))
    date_facture = Column(Date)
    mois_facture = Column(String(20))
    periode_debut = Column(Date)
    periode_fin = Column(Date)
    date_limite_paiement = Column(Date)
    montant_ht = Column(Numeric(12, 2))
    montant_tva = Column(Numeric(12, 2))
    montant_ttc = Column(Numeric(12, 2))
    montant_avance_credit = Column(Numeric(12, 2))
    montant_du = Column(Numeric(12, 2))
    est_duplicata = Column(Boolean, default=False)
    statut = Column(String(30), default="extraite")
    erreur_validation = Column(Text)

    # RATTACHER : remplace RattacherDB — colonne FK directe vers ENTITES
    entite_id = Column(Integer, ForeignKey("entites.id"), nullable=True)

    lignes = relationship("LigneFactureDB", back_populates="facture")
    fournisseur_rel = relationship("FournisseurDB", back_populates="factures")
    logs = relationship("LogDB", back_populates="facture")
    ocr_data = relationship("OCRDataDB", back_populates="facture", uselist=False)

    # RATTACHER : facture -> entite (1,1 - 1,N)
    entite_rel = relationship("EntiteDB", back_populates="factures")

    # LIER : côté inverse — une facture peut être référencée par une commande
    commande = relationship("CommandeAchatDB", back_populates="facture_rel", uselist=False)


class LigneFactureDB(Base):
    __tablename__ = "lignes_facture"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facture_id = Column(Integer, ForeignKey("factures.id"))
    description = Column(String(255))
    categorie = Column(String(50))
    date_debut = Column(Date)
    date_fin = Column(Date)
    montant_ht = Column(Numeric(12, 2))
    date_import = Column(DateTime)

    facture = relationship("FactureDB", back_populates="lignes")


# ===================================================================
# OCR_DATA — EXTRAIRE (1,1 - 1,1)
# ===================================================================
class OCRDataDB(Base):
    __tablename__ = "ocr_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), unique=True, nullable=False)
    texte_extrait = Column(Text)
    date_extraction = Column(DateTime)

    facture = relationship("FactureDB", back_populates="ocr_data")


# ===================================================================
# COMMANDES_ACHAT
# ===================================================================
class CommandeAchatDB(Base):
    __tablename__ = "commandes_achat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_bc = Column(String(50), unique=True)
    type_commande = Column(String(50))
    groupe_acheteurs = Column(String(100))
    type_imputation = Column(String(50))
    article_code_designation = Column(String(255))
    quantite = Column(Integer)
    date_livraison = Column(Date)
    compte_general = Column(String(50))
    centre_de_couts = Column(String(50))
    code_tva = Column(String(20))

    # LIER : remplace LierDB — colonne FK directe vers FACTURES
    facture_id = Column(Integer, ForeignKey("factures.id"), unique=True, nullable=True)

    receptions = relationship("ReceptionDB", back_populates="commande")
    logs = relationship("LogDB", back_populates="commande")

    # LIER : commande -> facture (1,1 - 1,1)
    facture_rel = relationship("FactureDB", back_populates="commande")


# ===================================================================
# RECEPTIONS
# ===================================================================
class ReceptionDB(Base):
    __tablename__ = "receptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_documentation = Column(Date)
    date_comptable = Column(Date)

    # RÉCEPTIONNER : remplace ReceptionnerDB — colonne FK directe vers COMMANDES_ACHAT
    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), nullable=False)

    commande = relationship("CommandeAchatDB", back_populates="receptions")
    logs = relationship("LogDB", back_populates="reception")


# ===================================================================
# ENTITES
# ===================================================================
class EntiteDB(Base):
    __tablename__ = "entites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_entite = Column(String(150), nullable=False)

    factures = relationship("FactureDB", back_populates="entite_rel")


# ===================================================================
# LOGS
# ===================================================================
class LogDB(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True)
    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), nullable=True)
    reception_id = Column(Integer, ForeignKey("receptions.id"), nullable=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)

    etape = Column(String(50))
    niveau = Column(String(20))
    action = Column(String(100))
    message = Column(Text)
    date_creation = Column(DateTime)

    facture = relationship("FactureDB", back_populates="logs")
    commande = relationship("CommandeAchatDB", back_populates="logs")
    reception = relationship("ReceptionDB", back_populates="logs")
    utilisateur_rel = relationship("UtilisateurDB", back_populates="logs")


class FactureRejetDB(Base):
    __tablename__ = "factures_rejets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_facture = Column(String(50))
    fournisseur = Column(String(150))
    raison = Column(String(255))
    donnees_brutes = Column(JSONB)
    date_rejet = Column(DateTime)