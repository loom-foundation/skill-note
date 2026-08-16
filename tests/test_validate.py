"""Tests for scripts/validate.py."""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate  # noqa: E402

WELL_FORMED = """---
id: garden:idea:7fjq3ka
name: A worked example
kind: idea
status: current
---

One statement of the note's substance.

## Relations

- addresses: [Another note](./other.md){id=garden:need:2cdd82z}
"""


def note(**overrides):
    """A well-formed note's text, with named parts overridden."""
    fields = {
        "id": "garden:idea:7fjq3ka",
        "name": "A worked example",
        "kind": "idea",
        "status": "current",
    }
    fields.update({k: v for k, v in overrides.items() if k in fields})
    body = overrides.get("body", "\n\nOne statement of the note's substance.\n")
    frontmatter = "\n".join("%s: %s" % (k, v) for k, v in fields.items())
    return "---\n%s\n---%s" % (frontmatter, body)


class FileValidationTest(unittest.TestCase):
    def check(self, text):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "note.md"
            path.write_text(text, encoding="utf-8")
            findings, identity = validate.validate_file(path)
            return findings, identity

    def errors(self, text):
        findings, _ = self.check(text)
        return [f.message for f in findings if f.level == validate.ERROR]

    def warnings(self, text):
        findings, _ = self.check(text)
        return [f.message for f in findings if f.level == validate.WARNING]

    def test_a_well_formed_note_passes(self):
        self.assertEqual(self.errors(WELL_FORMED), [])
        self.assertEqual(self.warnings(WELL_FORMED), [])

    def test_missing_frontmatter_is_an_error(self):
        self.assertTrue(self.errors("Just prose, no envelope.\n"))

    def test_unterminated_frontmatter_is_an_error(self):
        self.assertTrue(self.errors("---\nid: garden:idea:7fjq3ka\n"))

    def test_each_missing_required_field_is_an_error(self):
        for field in ("id", "name", "kind", "status"):
            text = WELL_FORMED.replace("%s: " % field, "x%s: " % field, 1)
            self.assertTrue(
                any("required" in e and field in e for e in self.errors(text)),
                "no error for missing %s" % field,
            )

    def test_id_must_have_three_segments(self):
        self.assertTrue(self.errors(note(id="garden:7fjq3ka")))

    def test_opaque_rejects_excluded_letters(self):
        errors = self.errors(note(id="garden:idea:7fjqlka"))
        self.assertTrue(any("i, l, o, u" in e for e in errors))

    def test_opaque_rejects_uppercase(self):
        self.assertTrue(self.errors(note(id="garden:idea:7FJQ3KA")))

    def test_namespace_must_be_lowercase(self):
        self.assertTrue(self.errors(note(id="Garden:idea:7fjq3ka")))

    def test_segment_shape_is_a_warning_not_an_error(self):
        text = note(id="garden:overlong:7fjq3ka")
        self.assertEqual(self.errors(text), [])
        self.assertTrue(any("display defect" in w for w in self.warnings(text)))

    def test_kind_token_shape_is_enforced(self):
        self.assertTrue(self.errors(note(kind="Idea")))
        self.assertTrue(self.errors(note(kind="user_story")))
        self.assertEqual(self.errors(note(kind="user-story")), [])

    def test_missing_blank_line_before_lead_is_an_error(self):
        errors = self.errors(note(body="\nThe lead.\n"))
        self.assertTrue(any("blank line" in e for e in errors))

    def test_two_blank_lines_before_lead_is_an_error(self):
        errors = self.errors(note(body="\n\n\nThe lead.\n"))
        self.assertTrue(any("blank line" in e for e in errors))

    def test_missing_lead_is_an_error(self):
        self.assertTrue(self.errors(note(body="\n")))

    def test_a_headed_lead_is_an_error(self):
        errors = self.errors(note(body="\n\n## Context\n\nProse.\n"))
        self.assertTrue(any("unheaded" in e for e in errors))

    def test_a_level_one_heading_is_an_error(self):
        errors = self.errors(note(body="\n\nThe lead.\n\n# Section\n"))
        self.assertTrue(any("level-1" in e for e in errors))

    def test_the_name_repeated_as_a_heading_is_an_error(self):
        errors = self.errors(note(body="\n\nThe lead.\n\n## A worked example\n"))
        self.assertTrue(any("never repeated" in e for e in errors))

    def test_headings_inside_code_fences_are_ignored(self):
        body = "\n\nThe lead.\n\n```\n# not a heading\n```\n"
        self.assertEqual(self.errors(note(body=body)), [])

    def test_an_unknown_field_is_a_warning_never_an_error(self):
        text = WELL_FORMED.replace(
            "status: current\n", "status: current\npersona: someone\n"
        )
        self.assertEqual(self.errors(text), [])
        self.assertTrue(any("persona" in w for w in self.warnings(text)))

    def test_field_order_is_recommended_never_required(self):
        text = WELL_FORMED.replace(
            "id: garden:idea:7fjq3ka\nname: A worked example\n",
            "name: A worked example\nid: garden:idea:7fjq3ka\n",
        )
        self.assertEqual(self.errors(text), [])
        self.assertTrue(any("recommended" in w for w in self.warnings(text)))


class TreeValidationTest(unittest.TestCase):
    def run_main(self, root):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = validate.main([root])
        return code

    def test_an_opaque_collision_within_a_namespace_is_an_error(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "one.md").write_text(WELL_FORMED, encoding="utf-8")
            (Path(root) / "two.md").write_text(
                WELL_FORMED.replace("A worked example", "Another"),
                encoding="utf-8",
            )
            self.assertEqual(self.run_main(root), 1)

    def test_distinct_namespaces_never_collide(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "one.md").write_text(WELL_FORMED, encoding="utf-8")
            (Path(root) / "two.md").write_text(
                WELL_FORMED.replace("garden:idea:", "meadow:idea:"),
                encoding="utf-8",
            )
            self.assertEqual(self.run_main(root), 0)

    def test_a_manifest_is_not_swept_as_a_note(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "manifest.md").write_text(
                "---\nnamespace: garden\nlayout: free\n---\n\n# Manifest\n",
                encoding="utf-8",
            )
            (Path(root) / "one.md").write_text(WELL_FORMED, encoding="utf-8")
            notes = validate.collect_notes(root)
            self.assertEqual([p.name for p in notes], ["one.md"])


class CliTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_help_exits_zero(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("exit codes", result.stdout)

    def test_a_valid_file_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "note.md"
            path.write_text(WELL_FORMED, encoding="utf-8")
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 0)

    def test_violations_exit_nonzero_and_are_reported(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "note.md"
            path.write_text(note(status=""), encoding="utf-8")
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("status", result.stdout)


if __name__ == "__main__":
    unittest.main()
