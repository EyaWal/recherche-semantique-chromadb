"""Stratégies de segmentation pour le corpus Tolkien.

Les fonctions de ce module travaillent en mémoire et ne modifient jamais les
fichiers sources.
"""

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path


DEFAULT_CHUNK_SIZE = 200
DEFAULT_OVERLAP = 40
SECTION_PATTERN = re.compile(
    r"^(?P<marks>={2,6})\s*(?P<title>.*?)\s*(?P=marks)\s*$",
    re.MULTILINE,
)
WORD_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True)
class Chunk:
    """Unité de texte prête à être analysée ou indexée."""

    chunk_id: str
    text: str
    source_document: str
    strategy: str
    position: int
    word_start: int
    word_end: int
    section_title: str | None = None
    section_path: tuple[str, ...] = ()

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def metadata(self) -> dict:
        """Retourne les métadonnées dans un format adapté à ChromaDB."""
        return {
            "source_document": self.source_document,
            "strategy": self.strategy,
            "position": self.position,
            "word_start": self.word_start,
            "word_end": self.word_end,
            "section_title": self.section_title or "",
            "section_path": " > ".join(self.section_path),
        }


def _stable_id(source_document: str, strategy: str, position: int) -> str:
    """Construit un identifiant déterministe à partir de données stables."""
    source = f"{source_document}|{strategy}|{position}".encode("utf-8")
    digest = hashlib.sha1(source).hexdigest()[:12]
    return f"{strategy}:{Path(source_document).stem}:{position:04d}:{digest}"


def _make_chunk(
    words: list[str],
    source_document: str,
    strategy: str,
    position: int,
    word_start: int,
    word_end: int,
    section_title: str | None = None,
    section_path: tuple[str, ...] = (),
) -> Chunk:
    text = " ".join(words[word_start:word_end]).strip()
    if not text:
        raise ValueError(f"Chunk vide pour {source_document}, position {position}")
    return Chunk(
        chunk_id=_stable_id(source_document, strategy, position),
        text=text,
        source_document=source_document,
        strategy=strategy,
        position=position,
        word_start=word_start,
        word_end=word_end,
        section_title=section_title,
        section_path=section_path,
    )


def _ranges(length: int, chunk_size: int, overlap: int) -> list[tuple[int, int]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size doit être positif")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap doit être compris entre 0 et chunk_size - 1")

    step = chunk_size - overlap
    return [
        (start, min(start + chunk_size, length))
        for start in range(0, length, step)
        if start < length
    ]


def chunk_fixed(
    text: str,
    source_document: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Découpe un document en fenêtres de mots chevauchantes."""
    words = WORD_PATTERN.findall(text)
    chunks = []
    for position, (start, end) in enumerate(_ranges(len(words), chunk_size, overlap)):
        chunks.append(
            _make_chunk(
                words,
                source_document,
                "fixed",
                position,
                start,
                end,
            )
        )
    validate_chunks(chunks, len(words))
    return chunks


def _section_blocks(
    text: str,
) -> tuple[list[tuple[list[str], str | None, tuple[str, ...], int]], set[int]]:
    """Retourne les sections informatives et les positions des titres structurels."""
    tokens = list(WORD_PATTERN.finditer(text))
    words = [token.group() for token in tokens]
    matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        return ([(words, None, (), 0)] if words else []), set()

    structural_indexes: set[int] = set()
    heading_ranges: list[tuple[int, int]] = []
    for match in matches:
        indexes = [
            index
            for index, token in enumerate(tokens)
            if match.start() <= token.start() and token.end() <= match.end()
        ]
        if indexes:
            structural_indexes.update(indexes)
            heading_ranges.append((indexes[0], indexes[-1] + 1))

    blocks = []
    path: list[str] = []
    first_heading_start = heading_ranges[0][0]
    preamble_indexes = list(range(first_heading_start))
    if preamble_indexes:
        blocks.append(([words[i] for i in preamble_indexes], None, (), preamble_indexes[0]))

    for index, match in enumerate(matches):
        if index >= len(heading_ranges):
            break
        heading_start, heading_end = heading_ranges[index]
        next_start = (
            heading_ranges[index + 1][0]
            if index + 1 < len(heading_ranges)
            else len(words)
        )
        level = len(match.group("marks"))
        title = match.group("title").strip()
        path = path[: level - 2]
        path.append(title)
        content_indexes = list(range(heading_end, next_start))
        if content_indexes:
            blocks.append(
                (
                    [words[i] for i in content_indexes],
                    title,
                    tuple(path),
                    content_indexes[0],
                )
            )

    return blocks, structural_indexes


def chunk_by_sections(
    text: str,
    source_document: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Découpe aux frontières de sections, puis subdivise les sections longues."""
    chunks = []
    position = 0
    words = WORD_PATTERN.findall(text)
    total_words = len(words)
    section_blocks, structural_indexes = _section_blocks(text)

    for section_words, title, path, section_start in section_blocks:
        for local_start, local_end in _ranges(len(section_words), chunk_size, overlap):
            start = section_start + local_start
            end = section_start + local_end
            chunks.append(
                _make_chunk(
                    words,
                    source_document,
                    "sections",
                    position,
                    start,
                    end,
                    section_title=title,
                    section_path=path,
                )
            )
            position += 1

    validate_chunks(chunks, total_words, excluded_word_indexes=structural_indexes)
    return chunks


def validate_chunks(
    chunks: list[Chunk],
    source_word_count: int,
    excluded_word_indexes: set[int] | None = None,
) -> None:
    """Vérifie les invariants essentiels avant toute indexation."""
    identifiers = [chunk.chunk_id for chunk in chunks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Identifiants de chunks dupliqués")
    if any(not chunk.text.strip() for chunk in chunks):
        raise ValueError("Un chunk est vide")

    covered = set()
    for chunk in chunks:
        if not 0 <= chunk.word_start < chunk.word_end <= source_word_count:
            raise ValueError(f"Position invalide pour {chunk.chunk_id}")
        covered.update(range(chunk.word_start, chunk.word_end))

    excluded = excluded_word_indexes or set()
    expected = set(range(source_word_count)) - excluded
    if covered != expected:
        missing = expected - covered
        raise ValueError(f"Perte de texte détectée : {len(missing)} mots non couverts")


def load_documents(directory: Path) -> dict[str, str]:
    """Charge les fichiers texte nettoyés dans un ordre stable."""
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(directory.glob("*.txt"))
    }
