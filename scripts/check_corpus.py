#!/usr/bin/env python3
"""Contrôle qualité des fichiers texte du corpus téléchargé."""

import argparse
import re
from pathlib import Path


WORD_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
HTML_PATTERN = re.compile(r"<[^>]+>")


def analyse_file(path: Path, minimum_words: int) -> dict:
    text = path.read_text(encoding="utf-8")
    words = WORD_PATTERN.findall(text)
    issues = []

    if not text.strip():
        issues.append("vide")
    if len(words) < minimum_words:
        issues.append(f"trop court (< {minimum_words} mots)")
    if text.lower().startswith("redirect to:"):
        issues.append("redirection")
    if HTML_PATTERN.search(text):
        issues.append("résidus HTML")
    if "�" in text:
        issues.append("caractère mal encodé")

    return {
        "fichier": path.name,
        "mots": len(words),
        "caracteres": len(text),
        "lignes": len(text.splitlines()),
        "problemes": ", ".join(issues) if issues else "aucun",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Vérifie les fichiers texte du corpus")
    parser.add_argument("--dir", default="donnees/brutes", help="Dossier du corpus")
    parser.add_argument("--minimum-words", type=int, default=100)
    args = parser.parse_args()

    files = sorted(Path(args.dir).glob("*.txt"))
    if not files:
        print(f"Aucun fichier .txt trouvé dans {args.dir}")
        return 1

    print(f"Corpus : {args.dir}")
    print(f"Seuil minimal : {args.minimum_words} mots")
    print("Fichier | Mots | Caractères | Lignes | Problèmes")
    print("--- | ---: | ---: | ---: | ---")

    has_issues = False
    for path in files:
        result = analyse_file(path, args.minimum_words)
        print(
            f"{result['fichier']} | {result['mots']} | "
            f"{result['caracteres']} | {result['lignes']} | {result['problemes']}"
        )
        has_issues |= result["problemes"] != "aucun"

    return 1 if has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
