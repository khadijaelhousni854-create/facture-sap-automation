import logging
import os

# Crée le dossier "logs" s'il n'existe pas encore
os.makedirs("logs", exist_ok=True)

# Configuration du logger
logger = logging.getLogger("sap_automation")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Écriture dans un fichier
    fichier_handler = logging.FileHandler("logs/sap_automation.log", encoding="utf-8")
    fichier_handler.setFormatter(formatter)
    logger.addHandler(fichier_handler)

    # Affichage dans la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
