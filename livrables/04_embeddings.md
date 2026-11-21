# 4. Fonctions d'embeddings choisies

Les embeddings sont générés avec la bibliothèque Sentence Transformers.

## Modèles utilisés

| Modèle | Dimension | Utilisation |
|---|---:|---|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Modèle léger et rapide |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Modèle plus riche et plus coûteux |

La méthode utilisée prend en charge :

- le chargement différé des modèles ;
- l'encodage par batch ;
- la normalisation des embeddings ;
- la vérification du nombre de vecteurs ;
- la vérification de la dimension attendue ;
- l'utilisation des modèles déjà présents dans le cache local.

Les deux modèles ont été testés sur trois phrases liées au corpus avec un
calcul de similarité cosinus.
