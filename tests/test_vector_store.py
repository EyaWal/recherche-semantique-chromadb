"""Tests de stockage et récupération avec une base ChromaDB temporaire."""

import tempfile
import unittest
from pathlib import Path

from src.chunking import chunk_fixed
from src.vector_store import ChromaVectorStore


class VectorStoreTests(unittest.TestCase):
    def test_upsert_reexecution_et_recuperation(self):
        chunks = chunk_fixed("Frodo porte l'Anneau vers Mordor.", "test.txt", 20, 0)
        embeddings = [[0.1, 0.2, 0.3] for _ in chunks]

        with tempfile.TemporaryDirectory() as directory:
            store = ChromaVectorStore(Path(directory))
            collection = store.create_collection("test_collection")
            store.upsert_chunks(collection, chunks, embeddings, batch_size=1)
            store.upsert_chunks(collection, chunks, embeddings, batch_size=1)

            self.assertEqual(collection.count(), len(chunks))
            store.verify_collection(collection, len(chunks), 3)
            result = store.get(collection, [chunks[0].chunk_id])
            self.assertEqual(result["documents"][0], chunks[0].text)
            self.assertEqual(result["metadatas"][0]["source_document"], "test.txt")
            self.assertEqual(len(result["embeddings"][0]), 3)

            query_result = store.query(collection, embeddings[0], n_results=1)
            self.assertEqual(len(query_result["documents"][0]), 1)
            self.assertEqual(len(query_result["metadatas"][0]), 1)


if __name__ == "__main__":
    unittest.main()
