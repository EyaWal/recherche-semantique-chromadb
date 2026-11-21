#!/usr/bin/env python3
"""Compare la similarité sémantique de deux modèles locaux."""

from math import sqrt
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embeddings import SentenceTransformerEmbedder  # noqa: E402


PHRASES = {
    "A": "Frodo carried the One Ring to Mordor.",
    "B": "The hobbit travelled to Mount Doom to destroy the Ring.",
    "C": "The Rohirrim defended Helm's Deep against Saruman's army.",
}


def cosine_similarity(first: list[float], second: list[float]) -> float:
    """Calcule la similarité cosinus de deux vecteurs."""
    if len(first) != len(second):
        raise ValueError("Les vecteurs doivent avoir la même dimension")
    first_norm = sqrt(sum(value * value for value in first))
    second_norm = sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        raise ValueError("La similarité cosinus est indéfinie pour un vecteur nul")
    dot_product = sum(left * right for left, right in zip(first, second))
    return dot_product / (first_norm * second_norm)


def compare_model(model_name: str) -> dict:
    """Charge un modèle local, encode les phrases et mesure les temps."""
    embedder = SentenceTransformerEmbedder(
        model_name,
        batch_size=3,
        local_files_only=True,
    )

    load_start = perf_counter()
    embedder.load()
    load_seconds = perf_counter() - load_start

    encode_start = perf_counter()
    vectors = embedder.encode(list(PHRASES.values()))
    encode_seconds = perf_counter() - encode_start
    by_label = dict(zip(PHRASES, vectors))

    similarities = {
        "A-B": cosine_similarity(by_label["A"], by_label["B"]),
        "A-C": cosine_similarity(by_label["A"], by_label["C"]),
        "B-C": cosine_similarity(by_label["B"], by_label["C"]),
    }
    return {
        "model": model_name,
        "dimension": embedder.expected_dimension,
        "load_seconds": load_seconds,
        "encode_seconds": encode_seconds,
        "similarities": similarities,
        "ab_is_greater_than_ac": similarities["A-B"] > similarities["A-C"],
    }


def print_result(result: dict) -> None:
    print(f"\nModèle : {result['model']}")
    print(f"Dimension : {result['dimension']}")
    print(f"Chargement : {result['load_seconds']:.3f} s")
    print(f"Encodage des 3 phrases : {result['encode_seconds']:.3f} s")
    print("\nComparaison       Similarité cosinus")
    print("----------------  ------------------")
    for pair, score in result["similarities"].items():
        print(f"{pair:<16}  {score:.4f}")
    verdict = "oui" if result["ab_is_greater_than_ac"] else "non"
    print(f"A-B supérieure à A-C : {verdict}")


def main() -> int:
    models = (
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-mpnet-base-v2",
    )
    for model_name in models:
        print_result(compare_model(model_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
