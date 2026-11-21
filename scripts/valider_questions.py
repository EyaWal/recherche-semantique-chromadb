#!/usr/bin/env python3
"""Valide la structure et les références du jeu de questions."""

import json
from pathlib import Path


FICHIER_QUESTIONS = Path("donnees/questions_evaluation.json")
DOSSIER_DOCUMENTS = Path("donnees/nettoyees")
CATEGORIES_AUTORISEES = {"factuelle", "contextuelle", "transversale"}
IDENTIFIANTS_ATTENDUS = {f"Q{numero:02d}" for numero in range(1, 11)}


def erreur(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    questions = json.loads(FICHIER_QUESTIONS.read_text(encoding="utf-8"))

    if not isinstance(questions, list) or len(questions) != 10:
        erreur("Le fichier doit contenir exactement 10 questions.")

    identifiants = {question.get("id") for question in questions}
    if identifiants != IDENTIFIANTS_ATTENDUS:
        erreur("Les identifiants doivent être exactement Q01 à Q10.")

    documents_existants = {path.name for path in DOSSIER_DOCUMENTS.glob("*.txt")}

    for question in questions:
        categorie = question.get("categorie")
        if categorie not in CATEGORIES_AUTORISEES:
            erreur(f"Catégorie invalide pour {question.get('id')}: {categorie}")

        directs = question.get("documents_directement_pertinents", [])
        lies = question.get("documents_lies", [])
        tous_les_documents = directs + lies

        if len(directs) != len(set(directs)):
            erreur(f"Doublon dans les documents directs de {question['id']}.")
        if len(lies) != len(set(lies)):
            erreur(f"Doublon dans les documents liés de {question['id']}.")
        if set(directs) & set(lies):
            erreur(f"Un document est à la fois direct et lié dans {question['id']}.")

        documents_absents = set(tous_les_documents) - documents_existants
        if documents_absents:
            erreur(
                f"Documents absents pour {question['id']}: "
                f"{sorted(documents_absents)}"
            )

        references = question.get("references", [])
        documents_references = {reference.get("document") for reference in references}
        if not set(directs) <= documents_references:
            erreur(
                f"Chaque document direct doit avoir une référence de passage "
                f"dans {question['id']}."
            )

        for reference in references:
            document = reference.get("document")
            ligne = reference.get("ligne")
            if document not in documents_existants:
                erreur(f"Référence vers un document absent : {document}")
            if not isinstance(ligne, int) or ligne < 1:
                erreur(f"Numéro de ligne invalide dans {question['id']}.")
            if not reference.get("passage", "").strip():
                erreur(f"Passage justificatif vide dans {question['id']}.")

    print("Validation réussie : 10 questions, catégories valides, aucun doublon et documents existants.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERREUR : {exc}")
        raise SystemExit(1)
