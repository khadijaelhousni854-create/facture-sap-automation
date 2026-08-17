from database import init_db, engine

try:
    init_db()
    print("Connexion PostgreSQL réussie")
    print("Tables créées : factures, bons_de_commande, logs")
except Exception as e:
    print("Échec de connexion à PostgreSQL")
    print(f"Détail de l'erreur : {e}")