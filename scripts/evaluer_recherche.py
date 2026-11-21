#!/usr/bin/env python3
"""Évalue la recherche sémantique de la collection fixe + MiniLM."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embeddings import SentenceTransformerEmbedder  # noqa: E402
from src.vector_store import ChromaVectorStore  # noqa: E402


MODELS = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}


def evaluate_question(question: dict, retrieved_documents: list[str]) -> dict:
    expected = set(question["documents_directement_pertinents"])
    retrieved = set(retrieved_documents)
    relevant_found = expected & retrieved
    precision = len(relevant_found) / len(retrieved) if retrieved else 0.0
    recall = len(relevant_found) / len(expected) if expected else 0.0
    return {
        "question_id": question["id"],
        "retrieved_documents": retrieved_documents,
        "relevant_found": sorted(relevant_found),
        "precision": precision,
        "recall": recall,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Évalue une collection ChromaDB")
    parser.add_argument("--k", type=int, default=5, help="Nombre de chunks retournés")
    parser.add_argument("--collection", required=True)
    parser.add_argument("--model", choices=tuple(MODELS), required=True)
    args = parser.parse_args()
    if args.k <= 0:
        raise ValueError("k doit être positif")

    questions_path = ROOT / "donnees" / "questions_evaluation.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    store = ChromaVectorStore(ROOT / "donnees" / "chromadb")
    collection = store.get_collection(args.collection)
    model_name = MODELS[args.model]
    embedder = SentenceTransformerEmbedder(model_name, local_files_only=True)

    evaluations = []
    for question in questions:
        query_embedding = embedder.encode([question["question"]])[0]
        result = store.query(collection, query_embedding, args.k)
        metadatas = result.get("metadatas", [[]])[0]
        retrieved_documents = [metadata["source_document"] for metadata in metadatas]
        evaluations.append(evaluate_question(question, retrieved_documents))

    print(f"Collection : {args.collection}")
    print(f"k : {args.k} chunks par question")
    print("\nQuestion  Documents retrouvés                         Précision  Rappel")
    print("--------  ------------------------------------------  ---------  ------")
    for evaluation in evaluations:
        documents = ", ".join(evaluation["retrieved_documents"])
        print(
            f"{evaluation['question_id']:<8}  {documents[:42]:<42}  "
            f"{evaluation['precision']:.2f}       {evaluation['recall']:.2f}"
        )

    mean_precision = sum(item["precision"] for item in evaluations) / len(evaluations)
    mean_recall = sum(item["recall"] for item in evaluations) / len(evaluations)
    print(f"\nPrécision moyenne : {mean_precision:.3f}")
    print(f"Rappel moyen : {mean_recall:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
