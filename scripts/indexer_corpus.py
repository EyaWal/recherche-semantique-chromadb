#!/usr/bin/env python3
"""Indexe la configuration fixe + MiniLM dans ChromaDB."""

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chunking import (  # noqa: E402
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    chunk_by_sections,
    chunk_fixed,
    load_documents,
)
from src.embeddings import SentenceTransformerEmbedder  # noqa: E402
from src.vector_store import ChromaVectorStore  # noqa: E402


MODELS = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}
COLLECTIONS = {
    ("fixed", "minilm"): ("fixe_minilm", 647),
    ("sections", "minilm"): ("sections_minilm", 836),
    ("fixed", "mpnet"): ("fixe_mpnet", 647),
    ("sections", "mpnet"): ("sections_mpnet", 836),
}
EXPECTED_DOCUMENTS = 40


def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def main() -> int:
    parser = argparse.ArgumentParser(description="Indexe une configuration du corpus")
    parser.add_argument("--strategy", choices=("fixed", "sections"), default="fixed")
    parser.add_argument("--model", choices=tuple(MODELS), default="minilm")
    parser.add_argument("--replace", action="store_true", help="Remplace la collection")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    model_name = MODELS[args.model]
    collection_name, expected_chunks = COLLECTIONS[(args.strategy, args.model)]

    documents = load_documents(ROOT / "donnees" / "nettoyees")
    if len(documents) != EXPECTED_DOCUMENTS:
        raise ValueError(f"{len(documents)} documents trouvés, {EXPECTED_DOCUMENTS} attendus")

    chunks = []
    for document, text in documents.items():
        chunks.extend(
            (
                chunk_fixed if args.strategy == "fixed" else chunk_by_sections
            )(
                text, document, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP
            )
        )
    if len(chunks) != expected_chunks:
        raise ValueError(f"{len(chunks)} chunks produits, {expected_chunks} attendus")

    store = ChromaVectorStore(ROOT / "donnees" / "chromadb")
    collection = store.create_collection(
        collection_name,
        metadata={"strategy": args.strategy, "model": model_name},
        replace=args.replace,
    )
    embedder = SentenceTransformerEmbedder(
        model_name,
        batch_size=args.batch_size,
        local_files_only=True,
    )

    for chunk_batch in batches(chunks, args.batch_size):
        texts = [chunk.text for chunk in chunk_batch]
        embeddings = embedder.encode(texts)
        store.upsert_chunks(collection, chunk_batch, embeddings, batch_size=args.batch_size)

    store.verify_collection(collection, expected_chunks, embedder.expected_dimension)
    print(f"Collection : {collection_name}")
    print(f"Documents sources : {len(documents)}")
    print(f"Chunks indexés : {collection.count()}")
    print(f"Dimension vérifiée : {embedder.expected_dimension}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
