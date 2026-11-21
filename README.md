# Recherche sémantique avec ChromaDB

Projet universitaire consacré aux bases de données vectorielles et à la
recherche sémantique avec ChromaDB. Le corpus porte sur **Le Seigneur des
Anneaux**, avec un focus sur la Guerre de l'Anneau.

L'objectif est de construire un pipeline reproductible :

```text
Corpus Tolkien Gateway
        ↓
Nettoyage des documents
        ↓
Segmentation en chunks
        ↓
Embeddings
        ↓
Indexation ChromaDB
        ↓
Recherche sémantique
        ↓
Évaluation
```

## Objectifs du TP

- constituer un corpus documentaire cohérent ;
- comparer un chunking fixe et un chunking basé sur les sections ;
- comparer deux modèles Sentence Transformers ;
- indexer les chunks dans ChromaDB ;
- évaluer la recherche sur 10 questions annotées ;
- analyser le compromis entre précision et rappel.

## Installation

Créer ou activer l'environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
.venv/bin/pip install -r requirements.txt
```

Les principales dépendances sont `chromadb` pour la base vectorielle,
`sentence-transformers` pour les embeddings, ainsi que `jupyter` et `pandas`
pour les expérimentations.

## Structure du projet

```text
.
├── donnees/
│   ├── brutes/       # Articles téléchargés, non versionnés
│   ├── nettoyees/    # Corpus nettoyé
│   ├── chromadb/     # Base ChromaDB persistante, non versionnée
│   ├── liste_articles.txt
│   └── questions_evaluation.json
├── notebooks/        # Expérimentations Jupyter
├── rapport/          # Rapport universitaire
├── resultats/        # Résultats générés
├── scripts/          # Programmes exécutables
├── src/              # Modules Python réutilisables
├── tests/            # Tests unitaires
├── .gitignore
├── requirements.txt
└── README.md
```

## Préparation du corpus

Le corpus comprend 40 articles Tolkien Gateway sélectionnés autour de la
Guerre de l'Anneau. Les titres sont listés dans
`donnees/liste_articles.txt`.

Le script `scripts/wiki_downloader.py` permet de rechercher et télécharger les
articles via l'API MediaWiki. Les fichiers bruts sont contrôlés puis nettoyés
avec `scripts/nettoyer_corpus.py`.

Résultat : 40 documents nettoyés, une redirection exclue (`One_Ring.txt`), les
titres de sections MediaWiki conservés et les marqueurs de référence HTML
supprimés.

Le jeu d'évaluation est conservé dans `donnees/questions_evaluation.json`. Il
contient 10 questions factuelles, contextuelles et transversales.

## Chunking

Deux stratégies sont disponibles dans `src/chunking.py`.

### Chunking fixe

- 200 mots par chunk ;
- chevauchement de 40 mots ;
- 647 chunks produits.

### Chunking par sections

- prise en compte des titres `== ... ==` et `=== ... ===` ;
- conservation du titre et du chemin de section dans les métadonnées ;
- sous-découpage des sections longues ;
- exclusion des titres isolés ;
- 836 chunks produits.

Analyser les deux stratégies :

```bash
.venv/bin/python scripts/analyser_chunking.py
```

## Embeddings

Deux modèles sont comparés :

| Modèle | Dimensions | Caractéristique |
|---|---:|---|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Plus léger et rapide |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Représentations plus riches, plus coûteuses |

Le module `src/embeddings.py` prend en charge le chargement différé, l'encodage
par batch et la vérification des dimensions.

Tester quelques phrases du corpus :

```bash
.venv/bin/python scripts/test_embeddings.py \
  --model sentence-transformers/all-MiniLM-L6-v2
```

La première exécution peut télécharger le modèle. Les scripts d'indexation et
d'évaluation utilisent ensuite le cache local.

## Indexation ChromaDB

Le module `src/vector_store.py` utilise `chromadb.PersistentClient`. La base
locale est stockée dans `donnees/chromadb/`.

L'indexeur `scripts/indexer_corpus.py` utilise `upsert` avec les identifiants
stables des chunks. Une réexécution ne crée donc pas de doublons.

Les quatre collections disponibles sont :

| Collection | Chunking | Modèle | Chunks | Dimensions |
|---|---|---|---:|---:|
| `fixe_minilm` | fixe | MiniLM | 647 | 384 |
| `sections_minilm` | sections | MiniLM | 836 | 384 |
| `fixe_mpnet` | fixe | MPNet | 647 | 768 |
| `sections_mpnet` | sections | MPNet | 836 | 768 |

Exemple d'indexation :

```bash
.venv/bin/python scripts/indexer_corpus.py \
  --strategy fixed --model minilm
```

Pour recréer explicitement une collection, ajouter `--replace`.

## Recherche et évaluation

Évaluer une collection sur les 10 questions :

```bash
.venv/bin/python scripts/evaluer_recherche.py \
  --collection fixe_minilm \
  --model minilm \
  --k 5
```

Le paramètre `k` indique le nombre de chunks retournés par question.

Comparer les quatre configurations avec `k=3`, `5`, `10` et `20` :

```bash
.venv/bin/python scripts/comparer_configurations.py
```

Les résultats sont enregistrés dans
`resultats/comparaison_configurations.json`.

Les métriques sont calculées au niveau des documents :

- **précision** : proportion des documents retrouvés qui sont pertinents ;
- **rappel** : proportion des documents pertinents qui ont été retrouvés.

## Résultats obtenus

À `k=5` :

| Collection | Précision | Rappel |
|---|---:|---:|
| `fixe_minilm` | 0,417 | 0,308 |
| `sections_minilm` | 0,425 | 0,350 |
| `fixe_mpnet` | 0,650 | 0,392 |
| `sections_mpnet` | 0,600 | 0,350 |

Observations principales : MPNet obtient de meilleurs résultats globaux que
MiniLM ; `fixe_mpnet` est la meilleure configuration à `k=5` ; augmenter `k`
améliore le rappel mais réduit généralement la précision ; `sections_mpnet`
obtient le meilleur rappel à `k=20` avec 0,533.

Les résultats détaillés et l'analyse méthodologique sont disponibles dans
`rapport/rapport.md`.

## Tests

Lancer tous les tests unitaires :

```bash
.venv/bin/python -m unittest discover -s tests
```

Les tests couvrent le chunking, les dimensions d'embeddings, l'insertion dans
ChromaDB, la réexécution sans doublons et la récupération de résultats.

## Limites

L'évaluation repose sur 10 questions et des documents pertinents annotés
manuellement. Elle mesure la qualité de la recherche documentaire, pas la
qualité d'une réponse générée par un modèle de langage.

Les données Tolkien Gateway et les bases ChromaDB locales ne doivent pas être
versionnées sans vérifier les droits de redistribution. Les fichiers bruts,
la base SQLite et l'environnement `.venv` sont exclus par `.gitignore`.

## Rapport

Le rapport provisoire se trouve dans `rapport/rapport.md`. Il présente la
méthode, les choix techniques, les résultats, les limites et les prochaines
étapes du TP.
