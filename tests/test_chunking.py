"""Tests unitaires des stratégies de segmentation."""

import unittest

from src.chunking import chunk_by_sections


class ChunkBySectionsTests(unittest.TestCase):
    def test_document_sans_titres(self):
        chunks = chunk_by_sections("Un document simple sans titre.", "document.txt")
        self.assertEqual(len(chunks), 1)
        self.assertIn("document", chunks[0].text)
        self.assertEqual(chunks[0].section_path, ())

    def test_section_vide(self):
        chunks = chunk_by_sections("== Vide ==\n== Suite ==\nUn contenu utile.", "document.txt")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].section_title, "Suite")
        self.assertNotIn("Vide", chunks[0].text)

    def test_deux_titres_consecutifs(self):
        chunks = chunk_by_sections("== A ==\n== B ==\nTexte de B.", "document.txt")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].section_path, ("B",))
        self.assertEqual(chunks[0].text, "Texte de B.")

    def test_section_courte(self):
        chunks = chunk_by_sections("== Histoire ==\nFrodo voyage.", "document.txt")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].section_title, "Histoire")
        self.assertNotEqual(chunks[0].text, "Histoire")

    def test_section_de_plus_de_200_mots(self):
        content = " ".join(f"mot{i}" for i in range(250))
        chunks = chunk_by_sections(f"== Histoire ==\n{content}", "document.txt")
        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(max(chunk.word_count for chunk in chunks), 200)
        self.assertEqual(chunks[0].section_path, ("Histoire",))

    def test_conservation_du_contenu_et_des_metadonnees(self):
        text = "== Histoire ==\nFrodo rencontre Sam.\n=== Voyage ===\nIls partent ensemble."
        chunks = chunk_by_sections(text, "Frodo_Baggins.txt")
        combined = " ".join(chunk.text for chunk in chunks)
        self.assertIn("Frodo rencontre Sam.", combined)
        self.assertIn("Ils partent ensemble.", combined)
        self.assertTrue(all(chunk.source_document == "Frodo_Baggins.txt" for chunk in chunks))
        self.assertTrue(all(chunk.strategy == "sections" for chunk in chunks))
        self.assertTrue(all(chunk.section_path for chunk in chunks))
        self.assertEqual(len({chunk.chunk_id for chunk in chunks}), len(chunks))


if __name__ == "__main__":
    unittest.main()
