# Recherche sémantique avec ChromaDB

Projet universitaire en français consacré à la recherche sémantique et aux bases de données vectorielles avec [ChromaDB](https://www.trychroma.com/).

Le corpus utilisé pour le TP porte sur **Le Seigneur des Anneaux**. L'objectif sera de transformer des documents textuels en représentations vectorielles, de les stocker dans ChromaDB, puis d'effectuer des recherches par similarité sémantique.

## Structure du projet

```text
.
├── donnees/       # Corpus source et données préparées
├── notebooks/     # Expérimentations et démonstrations Jupyter
├── rapport/       # Rapport universitaire et illustrations
├── resultats/     # Résultats de recherche, exports et figures générées
├── src/           # Code Python réutilisable
├── .gitignore     # Fichiers exclus du suivi Git
├── requirements.txt
└── README.md
```

## Installation

La liste des dépendances se trouve dans `requirements.txt`. L'environnement
Python utilisé pour le TP est `.venv`.

## État du projet

Le corpus Tolkien est préparé et nettoyé : 40 documents sont disponibles dans
`donnees/nettoyees/`. Deux stratégies de chunking ont été comparées : 647
chunks fixes et 836 chunks basés sur les sections MediaWiki.

Les deux modèles d'embeddings ont été testés : MiniLM produit des vecteurs de
384 dimensions et MPNet des vecteurs de 768 dimensions. Les quatre
configurations sont indexées dans ChromaDB et évaluées sur 10 questions.

Les résultats détaillés sont disponibles dans
`resultats/comparaison_configurations.json` et le rapport provisoire dans
`rapport/rapport.md`.

## Licence et corpus

Les données utilisées doivent respecter les consignes du cours et les droits applicables. Ne pas versionner de contenu protégé ou volumineux sans vérifier qu'il peut être distribué dans ce dépôt.
