# Recherche sémantique avec ChromaDB

## Compte rendu du TP

## 1. Choix du corpus

Le corpus choisi est constitué de 40 articles de Tolkien Gateway consacrés à
la Guerre de l'Anneau.

La sélection couvre :

- les personnages : Frodo, Samwise, Aragorn, Gandalf, Sauron, Saruman, etc. ;
- les lieux : Mordor, Minas Tirith, Moria, Isengard, Helm's Deep, etc. ;
- les objets : l'Anneau Unique, Andúril, Narsil, les palantíri, etc. ;
- les événements : le Conseil d'Elrond, la rupture de la Communauté, les
  batailles du Hornburg et des Champs du Pelennor, etc.

Après contrôle qualité :

- 40 documents ont été nettoyés ;
- la redirection `One_Ring.txt` a été exclue ;
- les titres de sections MediaWiki ont été conservés ;
- le marqueur HTML `<ref=Strider/>` a été supprimé.

## 2. Liste commentée des 10 requêtes

| Identifiant | Requête | Catégorie |
|---|---|---|
| Q01 | Où l’Anneau Unique a-t-il été forgé et pourquoi devait-il être détruit à cet endroit ? | Factuelle |
| Q02 | Comment Narsil est-elle devenue Andúril et quelle importance cette transformation a-t-elle pour Aragorn ? | Contextuelle |
| Q03 | Pourquoi le Conseil d’Elrond a-t-il conduit à la formation de la Communauté de l’Anneau ? | Contextuelle |
| Q04 | Quelles décisions ont provoqué la rupture de la Communauté à Parth Galen ? | Contextuelle |
| Q05 | Quel rôle Samwise joue-t-il dans la réussite de la quête ? | Transversale |
| Q06 | Comment les forces de Rohan ont-elles remporté la bataille du Hornburg ? | Factuelle |
| Q07 | Pourquoi la bataille des Champs du Pelennor constitue-t-elle un tournant de la guerre ? | Transversale |
| Q08 | Comment la géographie de Mordor influence-t-elle la stratégie de Sauron ? | Transversale |
| Q09 | Comment l’utilisation des palantíri a-t-elle influencé Saruman, Aragorn et Denethor ? | Transversale |
| Q10 | Comment la Guerre de l’Anneau se prolonge-t-elle dans la Comté après la chute de Sauron ? | Contextuelle |

Les questions factuelles ciblent une information précise. Les questions
contextuelles nécessitent de relier plusieurs passages d'un même événement.
Les questions transversales impliquent plusieurs personnages, lieux ou
événements et sont donc plus difficiles pour le moteur de recherche.

## 3. Méthodes de segmentation choisies

Deux stratégies de segmentation ont été retenues.

### 3.1. Chunking fixe

- 200 mots par chunk ;
- chevauchement de 40 mots ;
- nom du document source conservé ;
- 647 chunks produits sur les 40 documents.

Cette méthode produit des chunks de taille régulière et facilite la
comparaison entre documents.

### 3.2. Chunking par sections MediaWiki

- détection des titres `== ... ==` et `=== ... ===` ;
- conservation du titre et du chemin hiérarchique de la section ;
- sous-découpage des sections de plus de 200 mots ;
- chevauchement de 40 mots pour les sections longues ;
- exclusion des titres isolés ou des sections vides ;
- 836 chunks produits.

Chaque chunk possède un identifiant stable, son texte, le document source, la
stratégie, sa position et ses métadonnées de section.

## 4. Fonctions d'embeddings choisies

Les embeddings sont générés avec la bibliothèque Sentence Transformers.

| Modèle | Dimension | Utilisation |
|---|---:|---|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Modèle léger et rapide |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Modèle plus riche et plus coûteux |

L'encodage est effectué par lots afin de limiter la consommation mémoire. Les
dimensions des vecteurs sont vérifiées avant leur utilisation.

Les deux modèles ont été testés sur trois phrases liées au corpus avec un
calcul de similarité cosinus. Pour les deux modèles, la similarité entre les
phrases portant sur Frodo et l'Anneau est supérieure à celle mesurée avec la
phrase portant sur la bataille du Hornburg.

## 5. Rapport d'analyse des résultats

### 5.1. Indexation

Quatre collections ChromaDB persistantes ont été créées :

| Collection | Chunking | Modèle | Chunks | Dimensions |
|---|---|---|---:|---:|
| `fixe_minilm` | Fixe | MiniLM | 647 | 384 |
| `sections_minilm` | Sections | MiniLM | 836 | 384 |
| `fixe_mpnet` | Fixe | MPNet | 647 | 768 |
| `sections_mpnet` | Sections | MPNet | 836 | 768 |

Les identifiants stables des chunks sont utilisés pour éviter les doublons
lors d'une réindexation.

### 5.2. Méthode d'évaluation

Les 10 requêtes ont été encodées avec le modèle correspondant à chaque
collection. Les `k` chunks les plus proches ont été récupérés pour `k=3`, `5`,
`10` et `20`.

Les métriques sont calculées au niveau des documents après suppression des
doublons :

- précision : documents retrouvés et directement pertinents / documents
  retrouvés ;
- rappel : documents retrouvés et directement pertinents / documents
  directement pertinents attendus.

### 5.3. Résultats à k=5

| Collection | Précision | Rappel |
|---|---:|---:|
| `fixe_minilm` | 0,417 | 0,308 |
| `sections_minilm` | 0,425 | 0,350 |
| `fixe_mpnet` | 0,650 | 0,392 |
| `sections_mpnet` | 0,600 | 0,350 |

### 5.4. Influence de k

| Collection | k | Précision | Rappel |
|---|---:|---:|---:|
| `fixe_minilm` | 3 | 0,550 | 0,275 |
| `fixe_minilm` | 20 | 0,241 | 0,525 |
| `sections_minilm` | 3 | 0,583 | 0,350 |
| `sections_minilm` | 20 | 0,247 | 0,525 |
| `fixe_mpnet` | 3 | 0,667 | 0,325 |
| `fixe_mpnet` | 20 | 0,280 | 0,483 |
| `sections_mpnet` | 3 | 0,717 | 0,317 |
| `sections_mpnet` | 20 | 0,337 | 0,533 |

### 5.5. Analyse

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

### 5.6. Limites

L'évaluation repose sur 10 requêtes et des annotations manuelles. Elle mesure
la qualité de la recherche documentaire, mais pas la qualité d'une réponse
générée par un modèle de langage.

Les métriques sont calculées au niveau des documents alors que les résultats
initiaux sont des chunks. Cette agrégation évite de favoriser artificiellement
les documents possédant beaucoup de chunks, mais elle ne mesure pas le
classement des passages à l'intérieur d'un même document.

## Conclusion

La comparaison montre que le choix du modèle d'embeddings a un impact plus
important que la seule stratégie de segmentation sur ce corpus. MPNet obtient
les meilleurs résultats globaux. Le choix de `k` dépend toutefois de
l'objectif : une faible valeur favorise la précision, tandis qu'une valeur
plus élevée favorise le rappel.
