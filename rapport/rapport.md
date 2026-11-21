# Recherche sémantique avec ChromaDB

## 1. Objectif

Ce projet étudie une chaîne de recherche sémantique appliquée à un corpus
consacré à la Guerre de l'Anneau. L'objectif est de comparer deux stratégies
de segmentation et deux modèles d'embeddings avant d'évaluer la recherche
vectorielle avec ChromaDB.

## 2. Corpus

Le corpus est constitué de 40 articles Tolkien Gateway nettoyés. Une
redirection (`One_Ring.txt`) a été exclue. Les fichiers nettoyés sont conservés
dans `donnees/nettoyees/`.

Le jeu d'évaluation contient 10 questions factuelles, contextuelles et
transversales. Pour chaque question, les documents directement pertinents ont
été identifiés manuellement et servent de référence pour les métriques.

## 3. Stratégies de chunking

Deux stratégies ont été comparées :

- chunking fixe de 200 mots avec un chevauchement de 40 mots ;
- chunking basé sur les sections MediaWiki, avec sous-découpage des sections
  longues et conservation du chemin de section dans les métadonnées.

| Stratégie | Nombre de chunks | Moyenne |
|---|---:|---:|
| Fixe | 647 | 193,3 mots |
| Sections | 836 | 138,2 mots |

Le chunking par sections produit davantage de passages, mais conserve mieux la
structure thématique des articles.

## 4. Modèles d'embeddings

Les modèles testés sont :

- `sentence-transformers/all-MiniLM-L6-v2`, vecteurs de 384 dimensions ;
- `sentence-transformers/all-mpnet-base-v2`, vecteurs de 768 dimensions.

Les embeddings sont calculés par lots et les dimensions sont vérifiées avant
l'insertion dans ChromaDB.

## 5. Indexation ChromaDB

Quatre collections persistantes ont été créées dans `donnees/chromadb/` :

| Collection | Chunking | Modèle | Chunks | Dimensions |
|---|---|---|---:|---:|
| `fixe_minilm` | Fixe | MiniLM | 647 | 384 |
| `sections_minilm` | Sections | MiniLM | 836 | 384 |
| `fixe_mpnet` | Fixe | MPNet | 647 | 768 |
| `sections_mpnet` | Sections | MPNet | 836 | 768 |

Les identifiants stables des chunks sont utilisés avec `upsert`, ce qui permet
de réexécuter l'indexation sans créer de doublons.

## 6. Méthode d'évaluation

Chaque question est encodée avec le modèle correspondant à la collection. Les
`k` chunks les plus proches sont récupérés par ChromaDB. Les doublons de chunks
provenant du même document sont regroupés avant le calcul.

- **Précision** : proportion des documents retrouvés qui sont directement
  pertinents.
- **Rappel** : proportion des documents directement pertinents qui ont été
  retrouvés.

Les valeurs de `k` testées sont 3, 5, 10 et 20.

## 7. Résultats

| Collection | k | Précision | Rappel |
|---|---:|---:|---:|
| `fixe_minilm` | 3 | 0,550 | 0,275 |
| `fixe_minilm` | 5 | 0,417 | 0,308 |
| `fixe_minilm` | 10 | 0,353 | 0,367 |
| `fixe_minilm` | 20 | 0,241 | 0,525 |
| `sections_minilm` | 3 | 0,583 | 0,350 |
| `sections_minilm` | 5 | 0,425 | 0,350 |
| `sections_minilm` | 10 | 0,353 | 0,467 |
| `sections_minilm` | 20 | 0,247 | 0,525 |
| `fixe_mpnet` | 3 | 0,667 | 0,325 |
| `fixe_mpnet` | 5 | 0,650 | 0,392 |
| `fixe_mpnet` | 10 | 0,424 | 0,392 |
| `fixe_mpnet` | 20 | 0,280 | 0,483 |
| `sections_mpnet` | 3 | 0,717 | 0,317 |
| `sections_mpnet` | 5 | 0,600 | 0,350 |
| `sections_mpnet` | 10 | 0,516 | 0,417 |
| `sections_mpnet` | 20 | 0,337 | 0,533 |

## 8. Analyse

L'augmentation de `k` améliore généralement le rappel, car davantage de
documents sont examinés. En contrepartie, la précision diminue : les résultats
contiennent davantage de documents liés mais non directement pertinents.

MPNet obtient globalement de meilleurs résultats que MiniLM sur ce jeu de
questions. Avec `k=3`, `sections_mpnet` obtient la meilleure précision
(`0,717`). Avec `k=20`, cette même configuration obtient le meilleur rappel
(`0,533`).

Pour un moteur privilégiant les premiers résultats, `sections_mpnet` avec
`k=3` est intéressant. Pour limiter les documents manqués, `sections_mpnet`
avec `k=20` est préférable. Un réglage autour de `k=10` constitue un compromis
raisonnable entre précision et rappel.

## 9. Limites

L'évaluation repose sur 10 questions et sur des documents pertinents annotés
manuellement. Les métriques sont calculées au niveau du document, alors que
ChromaDB retourne des chunks. Cette agrégation évite de favoriser artificiellement
les documents possédant beaucoup de chunks, mais elle ne mesure pas la qualité
du classement à l'intérieur d'un même document.

Les scores ne mesurent pas encore la qualité d'une réponse générée : ils
mesurent uniquement la capacité à retrouver les documents de référence.

## 10. Prochaines étapes

Les prochaines étapes sont l'analyse détaillée des erreurs par question, la
production de tableaux ou graphiques pour le rapport final, puis éventuellement
l'ajout d'une génération de réponse séparée de la recherche documentaire.
