# Projet RPA IAM — Marsa Maroc (Stagiaire 3, étape 1)

## Contenu de ce dossier
- `src/models/database_models.py` : modèle des 3 tables (factures, bons_de_commande, logs)
- `src/database.py` : connexion et initialisation de la base SQLite
- `src/test_db_creation.py` : script pour créer et vérifier la base
- `requirements.txt` : dépendances Python

## Installation

```bash
pip install -r requirements.txt --break-system-packages
```

## Lancer le test de création de la base

Depuis le dossier `src/` :

```bash
cd src
python test_db_creation.py
```

Un fichier `projet_rpa.db` doit apparaître dans le dossier `src/`.
Tu peux l'ouvrir avec l'extension VS Code "SQLite Viewer" ou l'outil
"DB Browser for SQLite" pour vérifier visuellement les 3 tables créées.

## Prochaine étape
Une fois la base validée, créer l'API FastAPI (`main.py`) avec les
endpoints CRUD pour les factures.
