# verifier_connexion.py
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import DB_CONFIG
import psycopg2


def main():
    print("Tentative de connexion a :", DB_CONFIG["host"], "/", DB_CONFIG["dbname"])

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Connexion reussie\n")
    except Exception as e:
        print("[ECHEC] Connexion echouee")
        print(e)
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [t[0] for t in cur.fetchall()]

        print(f"Tables trouvees ({len(tables)}) :")
        for t in tables:
            print(f"  - {t}")

        tables_attendues = ["factures", "fournisseurs", "factures_rejets"]
        manquantes = [t for t in tables_attendues if t not in tables]

        print()
        if manquantes:
            print(f"[ATTENTION] Tables attendues manquantes : {manquantes}")
        else:
            print("[OK] Toutes les tables essentielles sont presentes")

    finally:
        conn.close()


if __name__ == "__main__":
    main()