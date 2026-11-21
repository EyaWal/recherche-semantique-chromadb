# 5. Rapport d'analyse des résultats

## Indexation

Quatre collections ChromaDB persistantes ont été créées :

| Collection | Chunking | Modèle | Chunks | Dimensions |
|---|---|---|---:|---:|
| `fixe_minilm` | Fixe | MiniLM | 647 | 384 |
| `sections_minilm` | Sections | MiniLM | 836 | 384 |
| `fixe_mpnet` | Fixe | MPNet | 647 | 768 |
| `sections_mpnet` | Sections | MPNet | 836 | 768 |

## Méthode d'évaluation

Les 10 requêtes ont été encodées avec le modèle correspondant à chaque
collection. ChromaDB a retourné les `k` chunks les plus proches pour `k=3`,
`5`, `10` et `20`.

Les métriques sont calculées au niveau des documents après suppression des
doublons :

- précision : documents retrouvés et directement pertinents / documents
  retrouvés ;
- rappel : documents retrouvés et directement pertinents / documents
  directement pertinents attendus.

## Résultats à k=5

| Collection | Précision | Rappel |
|---|---:|---:|
| `fixe_minilm` | 0,417 | 0,308 |
| `sections_minilm` | 0,425 | 0,350 |
| `fixe_mpnet` | 0,650 | 0,392 |
| `sections_mpnet` | 0,600 | 0,350 |

## Analyse

MPNet obtient de meilleurs résultats que MiniLM sur ce jeu d'évaluation. À
`k=5`, la configuration `fixe_mpnet` fournit le meilleur compromis entre
précision et rappel.

La configuration `sections_mpnet` obtient la meilleure précision à `k=3`
avec 0,717 et le meilleur rappel à `k=20` avec 0,533. Le chunking par sections
est donc intéressant lorsque l'objectif est de retrouver davantage de
documents pertinents, notamment pour les requêtes transversales.

L'augmentation de `k` augmente généralement le rappel, mais diminue la
précision, car des documents seulement liés sont progressivement ajoutés aux
résultats.

## Limites

L'évaluation repose sur 10 requêtes et des annotations manuelles. Elle mesure
la qualité de la recherche documentaire, mais pas la qualité d'une réponse
générée par un modèle de langage.

