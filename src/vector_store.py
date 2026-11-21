"""Gestion d'une collection ChromaDB contenant des chunks et leurs vecteurs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import chromadb

from src.chunking import Chunk


class ChromaVectorStore:
    """Façade minimale autour de PersistentClient pour le TP."""

    def __init__(self, persist_directory: Path):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

    def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        replace: bool = False,
    ) -> Any:
        """Crée ou récupère une collection, avec remplacement explicite possible."""
        if replace:
            try:
                self.client.delete_collection(name)
            except ValueError:
                pass
        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata,
            embedding_function=None,
        )

    def upsert_chunks(
        self,
        collection: Any,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
        batch_size: int = 64,
    ) -> None:
        """Insère ou met à jour les chunks par lots."""
        if len(chunks) != len(embeddings):
            raise ValueError("Le nombre de chunks et de vecteurs doit être identique")
        if batch_size <= 0:
            raise ValueError("batch_size doit être positif")

        ids = [chunk.chunk_id for chunk in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("Les identifiants de chunks sont dupliqués")

        for start in range(0, len(chunks), batch_size):
            end = start + batch_size
            batch_chunks = chunks[start:end]
            batch_embeddings = embeddings[start:end]
            collection.upsert(
                ids=[chunk.chunk_id for chunk in batch_chunks],
                documents=[chunk.text for chunk in batch_chunks],
                embeddings=[list(vector) for vector in batch_embeddings],
                metadatas=[chunk.metadata() for chunk in batch_chunks],
            )

    def verify_collection(
        self,
        collection: Any,
        expected_count: int,
        expected_dimension: int,
    ) -> None:
        """Vérifie le nombre d'éléments et la dimension d'un vecteur stocké."""
        actual_count = collection.count()
        if actual_count != expected_count:
            raise ValueError(
                f"Collection incorrecte : {actual_count} éléments, "
                f"{expected_count} attendus"
            )
        if actual_count == 0:
            raise ValueError("Impossible de vérifier la dimension d'une collection vide")

        sample = collection.get(limit=1, include=["embeddings"])
        vectors = sample.get("embeddings")
        if vectors is None or len(vectors) == 0:
            raise ValueError("Aucun embedding récupérable dans la collection")
        actual_dimension = len(vectors[0])
        if actual_dimension != expected_dimension:
            raise ValueError(
                f"Dimension incorrecte : {actual_dimension}, "
                f"{expected_dimension} attendues"
            )

    def get(self, collection: Any, ids: Sequence[str]) -> dict[str, Any]:
        """Récupère les documents, métadonnées et embeddings demandés."""
        return collection.get(
            ids=list(ids),
            include=["documents", "metadatas", "embeddings"],
        )

    def get_collection(self, name: str) -> Any:
        """Ouvre une collection existante sans la modifier."""
        return self.client.get_collection(name=name, embedding_function=None)

    def query(
        self,
        collection: Any,
        embedding: Sequence[float],
        n_results: int,
    ) -> dict[str, Any]:
        """Retourne les chunks les plus proches d'un vecteur de requête."""
        if n_results <= 0:
            raise ValueError("n_results doit être positif")
        return collection.query(
            query_embeddings=[list(embedding)],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
