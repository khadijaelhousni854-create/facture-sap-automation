"""
config.py — configuration centralisée.
"""
import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "ep-odd-frost-axah07j6.c-4.us-east-2.aws.neon.tech"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "neondb"),
    "user": os.environ.get("DB_USER", "neondb_owner"),
    "password": os.environ.get("DB_PASSWORD", "npg_HPdgyQio83AG"),
    "sslmode": os.environ.get("DB_SSLMODE", "require"),
}