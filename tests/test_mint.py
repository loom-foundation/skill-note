"""Tests for scripts/mint.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import mint  # noqa: E402


class DrawTest(unittest.TestCase):
    def test_draws_from_the_lawful_alphabet(self):
        for _ in range(50):
            opaque = mint.draw_opaque(7)
            self.assertEqual(len(opaque), 7)
            self.assertTrue(set(opaque) <= set(mint.ALPHABET))

    def test_alphabet_excludes_i_l_o_u_and_uppercase(self):
        self.assertEqual(set("ilou") & set(mint.ALPHABET), set())
        self.assertEqual(mint.ALPHABET, mint.ALPHABET.lower())
        self.assertEqual(len(mint.ALPHABET), 32)

    def test_respects_length(self):
        self.assertEqual(len(mint.draw_opaque(9)), 9)


class UniquenessTest(unittest.TestCase):
    def test_finds_an_opaque_present_in_the_tree(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "note.md").write_text(
                "id: garden:idea:7fjq3ka\n", encoding="utf-8"
            )
            self.assertTrue(mint.opaque_in_tree("7fjq3ka", [root]))
            self.assertTrue(mint.opaque_in_tree("7FJQ3KA", [root]))

    def test_misses_an_absent_opaque(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "note.md").write_text(
                "id: garden:idea:7fjq3ka\n", encoding="utf-8"
            )
            self.assertFalse(mint.opaque_in_tree("2cdd82z", [root]))

    def test_mint_avoids_collisions(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "note.md").write_text("7fjq3ka\n", encoding="utf-8")
            opaque = mint.mint([root], length=7)
            self.assertIsNotNone(opaque)
            self.assertNotEqual(opaque, "7fjq3ka")
            self.assertFalse(mint.opaque_in_tree(opaque, [root]))


class NamespaceTest(unittest.TestCase):
    def test_reads_the_namespace_from_the_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "manifest.md").write_text(
                "---\nnamespace: garden\nlayout: free\n---\n\n# Manifest\n",
                encoding="utf-8",
            )
            self.assertEqual(mint.read_namespace(root), "garden")

    def test_no_manifest_yields_none(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(mint.read_namespace(root))

    def test_rejects_an_uppercase_namespace(self):
        self.assertIsNotNone(mint.check_namespace("Garden"))
        self.assertIsNone(mint.check_namespace("garden"))


class SegmentTest(unittest.TestCase):
    def test_accepts_lawful_segments(self):
        # The schema fixes lowercase and two to five characters, no more.
        for segment in ("req", "spec", "need", "pers", "dg", "re1", "re-q"):
            self.assertIsNone(mint.check_segment(segment))

    def test_rejects_unlawful_segments(self):
        for segment in ("", "r", "toolong", "Req"):
            self.assertIsNotNone(mint.check_segment(segment))


class CliTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "mint.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_help_exits_zero(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--segment", result.stdout)

    def test_mints_an_opaque_for_a_corpus(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "note.md").write_text("7fjq3ka\n", encoding="utf-8")
            result = self.run_cli(root)
            self.assertEqual(result.returncode, 0)
            opaque = result.stdout.strip()
            self.assertEqual(len(opaque), 7)
            self.assertTrue(set(opaque) <= set(mint.ALPHABET))

    def test_mints_a_full_id_with_manifest_namespace(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "manifest.md").write_text(
                "---\nnamespace: garden\n---\n\n# Manifest\n", encoding="utf-8"
            )
            result = self.run_cli("--segment", "idea", root)
            self.assertEqual(result.returncode, 0)
            full_id = result.stdout.strip()
            namespace, segment, opaque = full_id.split(":")
            self.assertEqual(namespace, "garden")
            self.assertEqual(segment, "idea")
            self.assertEqual(len(opaque), 7)

    def test_segment_without_namespace_is_an_error(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.run_cli("--segment", "idea", root)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
