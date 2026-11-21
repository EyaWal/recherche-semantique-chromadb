#!/usr/bin/env python3
"""Encode quelques phrases du corpus avec un modèle sélectionné."""

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embeddings import SentenceTransformerEmbedder  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Test minimal d'un modèle d'embeddings")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        choices=(
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
        ),
    )
    parser.add_argument("--batch-size", type=int, default=3)
    args = parser.parse_args()

    source = ROOT / "donnees" / "nettoyees" / "Frodo_Baggins.txt"
    sentences = [
        line.strip()
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ][:3]

    embedder = SentenceTransformerEmbedder(args.model, batch_size=args.batch_size)
    vectors = embedder.encode(sentences)
    print(f"Modèle : {args.model}")
    print(f"Textes encodés : {len(sentences)}")
    print(f"Dimension vérifiée : {len(vectors[0])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

