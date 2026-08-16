"""
config.py — configuration centralisée.
"""

import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "factures_marsa"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "2005@Khadija1710"),  # <-- à remplacer
}

STATUT_A_VALIDER = "A_VALIDER"
STATUT_VALIDE = "VALIDE"
STATUT_REJETE = "REJETE"
STATUT_DOUBLON = "DOUBLON"