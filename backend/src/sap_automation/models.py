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
    """
    Représente une facture validée, prête à être traitée dans SAP.
    Champs à confirmer/ajuster une fois le format exact de
    GET /factures/{id} vu en détail avec le Stagiaire 3.
    """
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
    """
    Résultat du traitement d'une facture (après BC + réception).
    Le champ "statut" utilise exactement les valeurs attendues par
    l'API du Stagiaire 3 : "terminee" ou "erreur".
    """
    facture_id: str
    statut: str                          # "en_cours" | "terminee" | "erreur"
    bc_numero: Optional[str] = None
    reception_numero: Optional[str] = None
    message: Optional[str] = None
    type_erreur: Optional[str] = None    # ex: "session_expiree", "formulaire_rejete",
                                          # "timeout", "popup_inattendue"