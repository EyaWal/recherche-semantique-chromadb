"""Tests sans téléchargement des modèles d'embeddings."""

import unittest

from src.embeddings import SentenceTransformerEmbedder


class FakeModel:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, texts, **kwargs):
        return [[0.0] * self.dimension for _ in texts]


class EmbeddingsTests(unittest.TestCase):
    def test_dimensions_minilm_sans_chargement(self):
        embedder = SentenceTransformerEmbedder(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.assertEqual(embedder.expected_dimension, 384)
        self.assertIsNone(embedder._model)

    def test_dimensions_mpnet_avec_faux_modele(self):
        embedder = SentenceTransformerEmbedder("sentence-transformers/all-mpnet-base-v2")
        embedder._model = FakeModel(768)
        vectors = embedder.encode(["Frodo porte l'Anneau.", "Mordor est une terre hostile."])
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 768)

    def test_refuse_un_vecteur_de_mauvaise_dimension(self):
        embedder = SentenceTransformerEmbedder(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        with self.assertRaises(ValueError):
            embedder.validate_vectors([[0.0] * 768], expected_count=1)


if __name__ == "__main__":
    unittest.main()
