Module SAP Automation — Stagiaire 4

Documentation du module d'automatisation SAP Fiori (création du Bon de Commande et de la réception) via Playwright, dans le cadre du projet "Plateforme intelligente d'automatisation du traitement des factures fournisseurs et intégration SAP Fiori" (Marsa Maroc).

1. Rôle du module

Ce module est responsable de la dernière étape du pipeline de traitement des factures : une fois qu'une facture a été extraite (OCR), validée et stockée dans PostgreSQL par le groupe Data, ce module :

Récupère les données de la facture (à terme, via l'API du groupe Développement).
Ouvre SAP Fiori avec Playwright.
Crée le Bon de Commande (BC).
Crée la réception liée à ce BC.
Journalise chaque étape et renvoie un statut.

État actuel : les interactions réelles avec SAP Fiori ne sont pas encore implémentées. Le module fonctionne pour l'instant en mode simulation (mock), en attendant :

les accès à un environnement SAP Fiori de test,
le contrat d'API définitif avec le Stagiaire 3 (format d'échange des données facture / statuts).
2. Installation et lancement
bash
# Se placer dans le dossier du projet
cd projetStage

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Installer les dépendances
pip install playwright
playwright install

# Lancer le script principal (mode simulation)
python main.py

Un dossier logs/ est créé automatiquement au premier lancement ; il contient l'historique des traitements (logs/sap_automation.log).

3. Structure du projet
projetStage/
├── venv/                    Environnement virtuel Python
├── logs/                    Logs générés automatiquement
├── sap_automation/          Package principal du module
│   ├── __init__.py
│   ├── browser.py           Ouverture / fermeture du navigateur Playwright
│   ├── bc.py                Création du Bon de Commande (BC)
│   ├── reception.py         Création de la réception
│   ├── models.py            Structures de données (Facture, StatutTraitement)
│   ├── logger.py            Configuration de la journalisation
│   └── retry.py             Réessai automatique en cas d'échec
├── interface_web/
│   └── index.html           Tableau de bord de suivi des factures (mock)
├── test_playwright.py       Script de vérification de l'installation
└── main.py                  Point d'entrée / exécution du flux complet
4. Détail des fichiers
browser.py

Centralise le lancement et la fermeture du navigateur Chromium via Playwright. Fournit deux fonctions : lancer_navigateur() et fermer_navigateur(). C'est ici que sera ajoutée, plus tard, la connexion/authentification à SAP Fiori.

models.py

Définit deux structures de données (dataclasses) :

Facture : les données d'une facture validée (fournisseur, numéro, montants, lignes de détail).
StatutTraitement : le résultat d'un traitement (statut, numéro de BC, numéro de réception, message).

Ces structures sont une première proposition et devront être confirmées avec le Stagiaire 3 lors de la définition du contrat d'API.

bc.py

Contient creer_bon_de_commande(page, facture). Actuellement simulée (retourne un numéro de BC fictif BC-SIMULE-0001). À terme, cette fonction pilotera Playwright pour naviguer dans l'app Fiori de création de commande d'achat, remplir les champs et enregistrer.

reception.py

Contient creer_reception(page, facture, bc_numero). Même logique que bc.py, mais pour la réception liée à un BC existant. Actuellement simulée (retourne REC-SIMULE-0001).

logger.py

Configure un logger centralisé (sap_automation) qui écrit à la fois dans la console et dans logs/sap_automation.log. Répond à l'exigence du cahier des charges : "Journalisation, historique et reporting".

retry.py

Fournit retry_async(fonction, *args, max_tentatives, delai, **kwargs), qui réessaie automatiquement une fonction asynchrone en cas d'échec (utile pour absorber les lenteurs ou erreurs temporaires de SAP Fiori).

main.py

Point d'entrée qui orchestre le flux complet : lance le navigateur, appelle creer_bon_de_commande puis creer_reception (avec retry), affiche les résultats, ferme le navigateur. Utilise actuellement une facture de test codée en dur.

interface_web/index.html

Tableau de bord HTML/CSS/JS autonome affichant la liste des factures et leur statut de traitement (succès, en cours, échec, erreur SAP), avec filtres. Utilise des données simulées en JavaScript. À terme, les données mock seront remplacées par un appel fetch() vers l'API FastAPI réelle.

5. Flux actuel (mode simulation)
main.py
  └─ lancer_navigateur()                [browser.py]
  └─ creer_bon_de_commande(facture)     [bc.py]      → statut BC (mock)
  └─ creer_reception(facture, bc)       [reception.py] → statut réception (mock)
  └─ fermer_navigateur()                [browser.py]

Chaque étape est journalisée via logger.py, et les appels à bc.py / reception.py passent par retry_async() (jusqu'à 3 tentatives en cas d'échec).

6. Ce qu'il reste à faire (TODO)
 Contrat d'API avec le Stagiaire 3 : définir le format exact des données échangées (facture reçue, statut renvoyé) et le sens des appels (qui appelle qui).
 Accès à un environnement SAP Fiori de test.
 Cartographier le parcours manuel SAP (BC + réception) : captures d'écran, sélecteurs HTML, champs, boutons.
 Implémenter les vraies actions Playwright dans bc.py et reception.py (remplacer les blocs [MOCK]).
 Connecter interface_web/index.html à l'API réelle (remplacer les données mock par un fetch()).
 Gérer les cas d'erreur spécifiques à SAP (messages d'erreur Fiori, champs invalides, session expirée...).
7. Notes

Ce projet est le pilote pour le fournisseur IAM, mais la solution doit rester générique afin d'être étendue à d'autres fournisseurs par la suite (cf. cahier des charges).