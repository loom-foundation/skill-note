"""Every template under resources/templates/ passes the skill's own validator."""

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "resources" / "templates"
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402


def run_validator(paths):
    """Run validate.main on paths; returns (exit status, stdout findings)."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = validate.main([str(p) for p in paths])
    return status, out.getvalue()


def template_files():
    """The template notes: every markdown file there but the README."""
    return sorted(p for p in TEMPLATES.glob("*.md") if p.name != "README.md")


class TemplateTest(unittest.TestCase):
    def test_templates_exist(self):
        self.assertTrue(template_files(), "no templates under %s" % TEMPLATES)

    def test_the_sweep_covers_every_template(self):
        self.assertEqual(validate.collect_notes(TEMPLATES), template_files())

    def test_each_template_validates_with_no_findings(self):
        for path in template_files():
            with self.subTest(template=path.name):
                status, findings = run_validator([path])
                self.assertEqual(status, 0, findings)
                self.assertEqual(findings, "", findings)

    def test_the_tree_validates_whole_with_no_findings(self):
        status, findings = run_validator([TEMPLATES])
        self.assertEqual(status, 0, findings)
        self.assertEqual(findings, "", findings)


if __name__ == "__main__":
    unittest.main()
