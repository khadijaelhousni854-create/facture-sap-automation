from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


# ===================================================================
# NOUVELLE TABLE : FOURNISSEURS
# (remplace le champ texte "fournisseur" dans FactureDB)
# ===================================================================
class FournisseurDB(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(150), unique=True, nullable=False)

    factures = relationship("FactureDB", back_populates="fournisseur_rel")
    commandes = relationship("PasserDB", back_populates="fournisseur")


class FactureDB(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Champ texte brut issu de l'OCR (nom tel qu'extrait, avant rapprochement)
    fournisseur_nom_extrait = Column(String(150))
    # Nouvelle FK vers le fournisseur normalisé, une fois le rapprochement fait
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

    lignes = relationship("LigneFactureDB", back_populates="facture")
    fournisseur_rel = relationship("FournisseurDB", back_populates="factures")
    liaisons_reception = relationship("LierDB", back_populates="facture")
    logs = relationship("LogDB", back_populates="facture")
    ocr_data = relationship("OCRDataDB", back_populates="facture", uselist=False)


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
# NOUVELLE TABLE : OCR_DATA
# Relation EXTRAIRE : 1,1 côté FACTURES - 1,1 côté OCR_DATA
# => relation un-à-un stricte : chaque facture a au plus une entrée OCR_DATA,
#    et chaque entrée OCR_DATA appartient à exactement une facture
# ===================================================================
class OCRDataDB(Base):
    __tablename__ = "ocr_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), unique=True, nullable=False)
    texte_extrait = Column(Text)
    date_extraction = Column(DateTime)

    facture = relationship("FactureDB", back_populates="ocr_data")


# ===================================================================
# COMMANDES_ACHAT — remplace BonDeCommandeDB, avec tous les attributs du MLD
# Plus de facture_id direct : le lien passe par RECEPTIONS puis LIER
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

    fournisseurs = relationship("PasserDB", back_populates="commande")
    receptions = relationship("ReceptionnerDB", back_populates="commande")
    entites = relationship("RattacherDB", back_populates="commande")


# ===================================================================
# NOUVELLE TABLE : RECEPTIONS
# ===================================================================
class ReceptionDB(Base):
    __tablename__ = "receptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_documentation = Column(Date)
    date_comptable = Column(Date)

    commandes = relationship("ReceptionnerDB", back_populates="reception")
    factures = relationship("LierDB", back_populates="reception")


# ===================================================================
# NOUVELLE TABLE : ENTITES
# ===================================================================
class EntiteDB(Base):
    __tablename__ = "entites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_entite = Column(String(150), nullable=False)

    commandes = relationship("RattacherDB", back_populates="entite")


# ===================================================================
# TABLES ASSOCIATIVES (relations N,N du MCD)
# ===================================================================
class PasserDB(Base):
    """Fournisseur passe une commande (1,N - 0,N)"""
    __tablename__ = "passer"

    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), primary_key=True)
    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), primary_key=True)

    fournisseur = relationship("FournisseurDB", back_populates="commandes")
    commande = relationship("CommandeAchatDB", back_populates="fournisseurs")


class ReceptionnerDB(Base):
    """Une commande est réceptionnée (1,N - 0,N)"""
    __tablename__ = "receptionner"

    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), primary_key=True)
    reception_id = Column(Integer, ForeignKey("receptions.id"), primary_key=True)

    commande = relationship("CommandeAchatDB", back_populates="receptions")
    reception = relationship("ReceptionDB", back_populates="commandes")


class LierDB(Base):
    """Une facture est liée à une réception (0,N - 0,N)"""
    __tablename__ = "lier"

    facture_id = Column(Integer, ForeignKey("factures.id"), primary_key=True)
    reception_id = Column(Integer, ForeignKey("receptions.id"), primary_key=True)

    facture = relationship("FactureDB", back_populates="liaisons_reception")
    reception = relationship("ReceptionDB", back_populates="factures")


class RattacherDB(Base):
    """Une commande est rattachée à une entité (1,N - 1,N)"""
    __tablename__ = "rattacher"

    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), primary_key=True)
    entite_id = Column(Integer, ForeignKey("entites.id"), primary_key=True)

    commande = relationship("CommandeAchatDB", back_populates="entites")
    entite = relationship("EntiteDB", back_populates="commandes")


# ===================================================================
# LOGS — FK corrigée + champ utilisateur ajouté
# ===================================================================
class LogDB(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True)
    commande_id = Column(Integer, ForeignKey("commandes_achat.id"), nullable=True)
    reception_id = Column(Integer, ForeignKey("receptions.id"), nullable=True)

    etape = Column(String(50))
    niveau = Column(String(20))
    action = Column(String(100))
    utilisateur = Column(String(100))
    message = Column(Text)
    date_creation = Column(DateTime)

    facture = relationship("FactureDB", back_populates="logs")


class FactureRejetDB(Base):
    __tablename__ = "factures_rejets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_facture = Column(String(50))
    fournisseur = Column(String(150))
    raison = Column(String(255))
    donnees_brutes = Column(JSONB)
    date_rejet = Column(DateTime)
    