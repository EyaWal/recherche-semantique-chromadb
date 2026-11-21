#!/usr/bin/env python3
"""Compare les deux stratégies de chunking sur le corpus nettoyé."""

import argparse
from collections import Counter
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chunking import (  # noqa: E402
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    Chunk,
    chunk_by_sections,
    chunk_fixed,
    load_documents,
)


def analyse(chunks: list[Chunk]) -> dict:
    sizes = [chunk.word_count for chunk in chunks]
    return {
        "total": len(chunks),
        "moyenne": sum(sizes) / len(sizes) if sizes else 0,
        "minimum": min(sizes) if sizes else 0,
        "maximum": max(sizes) if sizes else 0,
        "par_document": Counter(chunk.source_document for chunk in chunks),
    }


def afficher_resultats(nom: str, chunks: list[Chunk]) -> None:
    statistiques = analyse(chunks)
    print(f"\n=== {nom} ===")
    print(f"Chunks : {statistiques['total']}")
    print(f"Mots par chunk : moyenne={statistiques['moyenne']:.1f}, "
          f"min={statistiques['minimum']}, max={statistiques['maximum']}")
    print("Chunks par document :")
    for document, nombre in sorted(statistiques["par_document"].items()):
        print(f"  {document}: {nombre}")

    exemples = [chunk for chunk in chunks if chunk.source_document == "Frodo_Baggins.txt"][:3]
    print("Exemples Frodo_Baggins.txt :")
    for chunk in exemples:
        section = " > ".join(chunk.section_path) or "(aucune section)"
        extrait = " ".join(chunk.text.split())[:240]
        print(
            f"  {chunk.chunk_id} | position={chunk.position} | "
            f"section={section} | mots={chunk.word_count}\n"
            f"    {extrait}..."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse deux stratégies de chunking")
    parser.add_argument("--dir", type=Path, default=ROOT / "donnees" / "nettoyees")
    parser.add_argument("--expected-documents", type=int, default=40)
    args = parser.parse_args()

    documents = load_documents(args.dir)
    if len(documents) != args.expected_documents:
        raise ValueError(
            f"{len(documents)} documents trouvés, {args.expected_documents} attendus"
        )

    chunks_fixed = []
    chunks_sections = []
    for document, text in documents.items():
        chunks_fixed.extend(
            chunk_fixed(
                text,
                document,
                chunk_size=DEFAULT_CHUNK_SIZE,
                overlap=DEFAULT_OVERLAP,
            )
        )
        chunks_sections.extend(
            chunk_by_sections(
                text,
                document,
                chunk_size=DEFAULT_CHUNK_SIZE,
                overlap=DEFAULT_OVERLAP,
            )
        )

    afficher_resultats("Stratégie A — chunking fixe", chunks_fixed)
    afficher_resultats("Stratégie B — sections MediaWiki", chunks_sections)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
