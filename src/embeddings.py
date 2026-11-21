"""Encodage de textes avec les modèles Sentence Transformers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Sequence


MODEL_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
}


@dataclass
class SentenceTransformerEmbedder:
    """Encodeur réutilisable avec chargement différé du modèle."""

    model_name: str
    batch_size: int = 32
    normalize_embeddings: bool = True
    device: str | None = None
    local_files_only: bool = False

    def __post_init__(self) -> None:
        if self.model_name not in MODEL_DIMENSIONS:
            supported = ", ".join(sorted(MODEL_DIMENSIONS))
            raise ValueError(f"Modèle non supporté. Modèles disponibles : {supported}")
        if self.batch_size <= 0:
            raise ValueError("batch_size doit être positif")
        self._model: Any | None = None

    @property
    def expected_dimension(self) -> int:
        """Dimension attendue pour le modèle sélectionné."""
        return MODEL_DIMENSIONS[self.model_name]

    def load(self) -> Any:
        """Charge le modèle uniquement lors du premier encodage."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError(
                    "sentence-transformers doit être installé pour charger un modèle"
                ) from error
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                local_files_only=self.local_files_only,
            )
        return self._model

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode une séquence de textes par lots et vérifie les dimensions."""
        if any(not text.strip() for text in texts):
            raise ValueError("Les textes à encoder doivent être non vides")
        if not texts:
            return []

        model = self.load()
        vectors = model.encode(
            list(texts),
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )
        result = [
            vector.tolist() if hasattr(vector, "tolist") else list(vector)
            for vector in vectors
        ]
        self.validate_vectors(result, len(texts))
        return result

    def validate_vectors(
        self, vectors: Sequence[Sequence[float]], expected_count: int | None = None
    ) -> None:
        """Vérifie le nombre, la dimension et la validité numérique des vecteurs."""
        if expected_count is not None and len(vectors) != expected_count:
            raise ValueError(
                f"{len(vectors)} vecteurs produits pour {expected_count} textes"
            )
        for index, vector in enumerate(vectors):
            if len(vector) != self.expected_dimension:
                raise ValueError(
                    f"Le vecteur {index} a {len(vector)} dimensions, "
                    f"{self.expected_dimension} attendues"
                )
            if not all(isfinite(float(value)) for value in vector):
                raise ValueError(f"Le vecteur {index} contient une valeur non finie")

