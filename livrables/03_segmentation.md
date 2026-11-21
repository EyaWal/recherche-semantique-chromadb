# 3. Méthodes de segmentation choisies

Deux stratégies de segmentation ont été retenues.

## Chunking fixe

- 200 mots par chunk ;
- chevauchement de 40 mots ;
- nom du document source conservé ;
- 647 chunks produits sur les 40 documents.

Cette méthode produit des chunks de taille régulière et facilite la
comparaison entre documents.

## Chunking par sections MediaWiki

- détection des titres `== ... ==` et `=== ... ===` ;
- conservation du titre et du chemin hiérarchique de la section ;
- sous-découpage des sections de plus de 200 mots ;
- chevauchement de 40 mots pour les sections longues ;
- exclusion des titres isolés ou des sections vides ;
- 836 chunks produits.

Chaque chunk possède un identifiant stable, son texte, le document source, la
stratégie, sa position et ses métadonnées de section.

