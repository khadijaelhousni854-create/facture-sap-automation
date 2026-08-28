
""" config.py — configuration centralisée. """
import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5433)),
    "dbname": os.environ.get("DB_NAME", "marsa_factures"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "marsa123"),
    "sslmode": os.environ.get("DB_SSLMODE", "disable"),
}