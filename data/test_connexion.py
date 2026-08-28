from config import DB_CONFIG
import psycopg2

print("DB_CONFIG utilisé par Python :", DB_CONFIG)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, inet_server_port();")
        print("Connecté à :", cur.fetchone())
    conn.close()
except UnicodeDecodeError as e:
    print("Message d'erreur brut (décodé en cp1252) :")
    print(e.object.decode("cp1252", errors="replace"))
except Exception as e:
    print("Erreur :", e)