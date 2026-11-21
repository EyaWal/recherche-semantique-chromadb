#!/usr/bin/env python3
"""Compare les quatre configurations ChromaDB sur plusieurs valeurs de k."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embeddings import SentenceTransformerEmbedder  # noqa: E402
from src.vector_store import ChromaVectorStore  # noqa: E402


CONFIGURATIONS = (
    ("fixe_minilm", "fixed", "minilm"),
    ("sections_minilm", "sections", "minilm"),
    ("fixe_mpnet", "fixed", "mpnet"),
    ("sections_mpnet", "sections", "mpnet"),
)
MODELS = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}
K_VALUES = (3, 5, 10, 20)


def metrics(question: dict, retrieved_documents: list[str]) -> tuple[float, float]:
    expected = set(question["documents_directement_pertinents"])
    retrieved = set(retrieved_documents)
    relevant = expected & retrieved
    precision = len(relevant) / len(retrieved) if retrieved else 0.0
    recall = len(relevant) / len(expected) if expected else 0.0
    return precision, recall


def main() -> int:
    questions = json.loads(
        (ROOT / "donnees" / "questions_evaluation.json").read_text(encoding="utf-8")
    )
    store = ChromaVectorStore(ROOT / "donnees" / "chromadb")
    rows = []

    for collection_name, strategy, model_key in CONFIGURATIONS:
        collection = store.get_collection(collection_name)
        embedder = SentenceTransformerEmbedder(
            MODELS[model_key], batch_size=32, local_files_only=True
        )
        query_vectors = embedder.encode([question["question"] for question in questions])
        retrieved_by_question = []
        for vector in query_vectors:
            result = store.query(collection, vector, max(K_VALUES))
            metadatas = result.get("metadatas", [[]])[0]
            retrieved_by_question.append(
                [metadata["source_document"] for metadata in metadatas]
            )

        for k in K_VALUES:
            scores = [
                metrics(question, retrieved[:k])
                for question, retrieved in zip(questions, retrieved_by_question)
            ]
            rows.append(
                {
                    "collection": collection_name,
                    "strategy": strategy,
                    "model": model_key,
                    "k": k,
                    "precision_moyenne": sum(score[0] for score in scores) / len(scores),
                    "rappel_moyen": sum(score[1] for score in scores) / len(scores),
                }
            )

    output_path = ROOT / "resultats" / "comparaison_configurations.json"
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Configuration       k   Précision   Rappel")
    print("------------------  --  ----------  ------")
    for row in rows:
        print(
            f"{row['collection']:<18}  {row['k']:>2}  "
            f"{row['precision_moyenne']:.3f}       {row['rappel_moyen']:.3f}"
        )
    print(f"\nRésultats enregistrés dans : {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
