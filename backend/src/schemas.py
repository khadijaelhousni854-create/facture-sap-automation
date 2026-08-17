from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class LigneFactureCreate(BaseModel):
    description: str
    categorie: str
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    montant_ht: float


class FactureCreate(BaseModel):
    # Renommé pour correspondre à FactureDB : c'est le texte brut extrait par l'OCR,
    # avant tout rapprochement avec un FournisseurDB normalisé.
    fournisseur_nom_extrait: str
    # Optionnel : peut être renseigné directement si le fournisseur est déjà connu/rapproché.
    fournisseur_id: Optional[int] = None

    client: str
    numero_client: str
    numero_facture: str
    type_facture: str
    source_fichier: Optional[str] = None

    numero_abonnement: Optional[str] = None
    numero_appel: Optional[str] = None

    date_facture: date
    mois_facture: Optional[str] = None
    periode_debut: Optional[date] = None
    periode_fin: Optional[date] = None
    date_limite_paiement: Optional[date] = None

    montant_ht: float
    montant_tva: float
    montant_ttc: float
    montant_avance_credit: Optional[float] = 0
    montant_du: Optional[float] = None

    est_duplicata: Optional[bool] = False

    lignes: Optional[List[LigneFactureCreate]] = []


class FactureResponse(FactureCreate):
    id: int
    statut: str
    erreur_validation: Optional[str] = None

    class Config:
        from_attributes = True


class StatutUpdate(BaseModel):
    statut: str
    numero_bc: Optional[str] = None


class LogResponse(BaseModel):
    id: int
    # Devenus optionnels : un log peut concerner une facture, une commande,
    # ou une réception (jamais tous les trois en même temps en général).
    facture_id: Optional[int] = None
    commande_id: Optional[int] = None
    reception_id: Optional[int] = None
    etape: str
    niveau: str
    action: Optional[str] = None
    utilisateur: Optional[str] = None
    message: str
    date_creation: datetime

    class Config:
        from_attributes = True


class FactureRejetCreate(BaseModel):
    numero_facture: str
    fournisseur: str
    raison: str
    donnees_brutes: dict


class FactureRejetResponse(FactureRejetCreate):
    id: int
    date_rejet: datetime

    class Config:
        from_attributes = True


# ===================================================================
# NOUVEAUX SCHEMAS — pour les routes ajoutées (fournisseurs, entites, ocr)
# ===================================================================
class FournisseurResponse(BaseModel):
    id: int
    nom: str

    class Config:
        from_attributes = True


class EntiteResponse(BaseModel):
    id: int
    nom_entite: str

    class Config:
        from_attributes = True


class OCRDataResponse(BaseModel):
    id: int
    facture_id: int
    texte_extrait: Optional[str] = None
    date_extraction: datetime

    class Config:
        from_attributes = True
class CommandeAchatCreate(BaseModel):
    numero_bc: str
    type_commande: Optional[str] = None
    groupe_acheteurs: Optional[str] = None
    type_imputation: Optional[str] = None
    article_code_designation: Optional[str] = None
    quantite: Optional[int] = None
    date_livraison: Optional[date] = None
    compte_general: Optional[str] = None
    centre_de_couts: Optional[str] = None
    code_tva: Optional[str] = None


class CommandeAchatResponse(CommandeAchatCreate):
    id: int

    class Config:
        from_attributes = True


class ReceptionCreate(BaseModel):
    date_documentation: Optional[date] = None
    date_comptable: Optional[date] = None


class ReceptionResponse(ReceptionCreate):
    id: int

    class Config:
        from_attributes = True