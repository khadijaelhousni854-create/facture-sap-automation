# src/config.py
"""
Configuration centralisÃ©e pour le projet d'automatisation des factures
"""

import os
from pathlib import Path

# Project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
print(f"PROJECT_ROOT = {PROJECT_ROOT}")

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"  # PDFs input
OUTPUT_DIR = DATA_DIR / "output"    # JSON output

# Create output dir if doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OCR Configuration
OCR_CONFIG = {
    "lang": "fr",
    "use_angle_cls": True,
}

# Extraction fields - les 6 champs qu'on cherche
REQUIRED_FIELDS = [
    "fournisseur",
    "numero_facture",
    "date",
    "montant_ht",
    "montant_tva",
    "montant_ttc"
]

# Logging
LOG_LEVEL = "INFO"
