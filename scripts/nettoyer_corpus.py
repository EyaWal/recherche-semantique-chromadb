#!/usr/bin/env python3
"""Nettoyage minimal et reproductible du corpus Tolkien."""

from pathlib import Path
import re


DOSSIER_SOURCE = Path("donnees/brutes")
DOSSIER_DESTINATION = Path("donnees/nettoyees")
NOMBRE_DOCUMENTS_ATTENDUS = 40

# Exemple : <ref=Strider/> ou <ref=source/>.
MARQUEUR_REFERENCE = re.compile(r"<ref=[^>]+/>")


def est_redirection(texte: str) -> bool:
    """Retourne True si le fichier contient uniquement une redirection wiki."""
    return bool(re.fullmatch(r"Redirect to:\s*.+", texte.strip(), flags=re.IGNORECASE))


def nettoyer_document(texte: str) -> tuple[str, int]:
    """Supprime les références ciblées et retourne le texte ainsi que le compteur."""
    texte_nettoye, nombre_supprime = MARQUEUR_REFERENCE.subn("", texte)
    return texte_nettoye, nombre_supprime


def main() -> int:
    fichiers_source = sorted(DOSSIER_SOURCE.glob("*.txt"))
    DOSSIER_DESTINATION.mkdir(parents=True, exist_ok=True)

    fichiers_exclus: list[str] = []
    documents_traites = 0
    marqueurs_supprimes = 0

    for fichier_source in fichiers_source:
        texte = fichier_source.read_text(encoding="utf-8")

        if est_redirection(texte):
            fichiers_exclus.append(fichier_source.name)
            continue

        texte_nettoye, nombre_supprime = nettoyer_document(texte)
        fichier_destination = DOSSIER_DESTINATION / fichier_source.name
        fichier_destination.write_text(texte_nettoye, encoding="utf-8")

        documents_traites += 1
        marqueurs_supprimes += nombre_supprime

    print(f"Documents traités : {documents_traites}")
    print(f"Fichiers exclus : {fichiers_exclus or 'aucun'}")
    print(f"Marqueurs de référence supprimés : {marqueurs_supprimes}")
    print(f"Documents attendus : {NOMBRE_DOCUMENTS_ATTENDUS}")

    if documents_traites != NOMBRE_DOCUMENTS_ATTENDUS:
        print(
            "ERREUR : le nombre de documents nettoyés ne correspond pas "
            "au nombre attendu."
        )
        return 1

    print("Vérification réussie : les 40 documents attendus sont nettoyés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
