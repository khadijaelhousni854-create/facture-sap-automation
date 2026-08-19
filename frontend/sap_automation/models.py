from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LigneFacture:
    """Une ligne de détail dans une facture (produit/service facturé)."""
    description: str
    quantite: float
    prix_unitaire: float


@dataclass
class Facture:
    """Représente une facture validée, prête à être traitée dans SAP."""
    facture_id: str
    fournisseur: str
    numero_facture: str
    date_facture: str          # format "YYYY-MM-DD"
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    lignes: list[LigneFacture] = field(default_factory=list)


@dataclass
class StatutTraitement:
    """Résultat du traitement d'une facture (après BC + réception)."""
    facture_id: str
    statut: str                          # "en_cours" | "succes" | "echec" | "erreur_sap"
    bc_numero: Optional[str] = None
    reception_numero: Optional[str] = None
    message: Optional[str] = None
