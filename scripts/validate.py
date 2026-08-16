#!/usr/bin/env python3
"""Validate Note files against what the method fixes today.

Checks the file envelope, the required frontmatter, the id grammar, and
the blank-line-and-lead rule, for one file or for every note in a corpus
tree; a tree is also swept for opaque collisions within a namespace.
Python 3.9, standard library only.
"""

import argparse
import re
import sys
from pathlib import Path

# Crockford Base32, lowercase: digits and letters minus i, l, o, u.
ALPHABET = set("0123456789abcdefghjkmnpqrstvwxyz")

REQUIRED_FIELDS = ("id", "name", "kind", "status")
KIND_RE = re.compile(r"^[a-z]+(-[a-z]+)*$")
KEY_RE = re.compile(r"^([^\s:#][^:]*):\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})(?:\s+(.*?))?\s*#*\s*$")

ERROR = "error"
WARNING = "warning"


class Finding:
    """One reported violation or advisory."""

    def __init__(self, path, level, message):
        self.path = path
        self.level = level
        self.message = message

    def __str__(self):
        return "%s: %s: %s" % (self.path, self.level, self.message)


def unquote(value):
    """Strip one pair of matching single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse(text):
    """Split a note into frontmatter fields and body lines.

    Returns (fields, order, body_lines, problems): the top-level scalar
    fields by key, the keys in file order, the body's lines, and any
    envelope problems as messages.
    """
    problems = []
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, [], [], ["no frontmatter: the file must open with ---"]
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        return None, [], [], ["unterminated frontmatter: no closing ---"]

    fields = {}
    order = []
    for raw in lines[1:closing]:
        if not raw.strip():
            continue
        if raw[0] in " \t-":
            continue  # a list item or nested content of the previous key
        match = KEY_RE.match(raw)
        if not match:
            problems.append("unreadable frontmatter line: %r" % raw)
            continue
        key = match.group(1).strip()
        if key in fields:
            problems.append("duplicate frontmatter field: %s" % key)
            continue
        fields[key] = unquote(match.group(2).strip())
        order.append(key)
    return fields, order, lines[closing + 1:], problems


def check_id(value, path, findings):
    """Check the id grammar: namespace, kind-segment, opaque."""
    parts = value.split(":")
    if len(parts) != 3 or not all(parts):
        findings.append(Finding(
            path, ERROR,
            "id must be <namespace>:<kind-segment>:<opaque>, got %r" % value,
        ))
        return None
    namespace, segment, opaque = parts
    if namespace != namespace.lower() or any(c.isspace() for c in namespace):
        findings.append(Finding(
            path, ERROR,
            "id namespace must be lowercase without whitespace: %r" % namespace,
        ))
    bad = sorted(set(opaque) - ALPHABET)
    if bad:
        findings.append(Finding(
            path, ERROR,
            "id opaque must be lowercase Crockford Base32 without i, l, o, u; "
            "unlawful characters %s in %r" % (", ".join(map(repr, bad)), opaque),
        ))
    if not (2 <= len(segment) <= 5 and segment == segment.lower()):
        findings.append(Finding(
            path, WARNING,
            "id kind-segment is a display defect: expected lowercase, "
            "two to five characters, got %r" % segment,
        ))
    return namespace, opaque


def check_body(body_lines, name, path, findings):
    """Check the blank-line-and-lead rule and the heading rules."""
    if not body_lines or not any(line.strip() for line in body_lines):
        findings.append(Finding(path, ERROR, "missing lead: the body is empty"))
        return
    if body_lines[0].strip():
        findings.append(Finding(
            path, ERROR,
            "exactly one blank line must separate the closing --- from the lead",
        ))
    elif len(body_lines) < 2 or not body_lines[1].strip():
        findings.append(Finding(
            path, ERROR,
            "exactly one blank line must separate the closing --- from the "
            "lead; found more than one",
        ))
    lead = next((line for line in body_lines if line.strip()), "")
    if lead.lstrip().startswith("#"):
        findings.append(Finding(
            path, ERROR,
            "the lead is unheaded: the body opens with one statement of "
            "substance, not a heading",
        ))

    fenced = False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level, text = len(match.group(1)), (match.group(2) or "").strip()
        if level == 1:
            findings.append(Finding(
                path, ERROR, "no level-1 heading is allowed in the body",
            ))
        if name and text == name:
            findings.append(Finding(
                path, ERROR, "the name is never repeated as a heading",
            ))


def validate_file(path):
    """Validate one note file. Returns (findings, identity or None)."""
    findings = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Finding(path, ERROR, "not valid UTF-8")], None
    except OSError as exc:
        return [Finding(path, ERROR, "unreadable: %s" % exc)], None

    fields, order, body_lines, problems = parse(text)
    for problem in problems:
        findings.append(Finding(path, ERROR, problem))
    if fields is None:
        return findings, None

    for key in REQUIRED_FIELDS:
        if key not in fields:
            findings.append(Finding(
                path, ERROR, "missing required frontmatter field: %s" % key,
            ))
        elif not fields[key]:
            findings.append(Finding(
                path, ERROR, "required frontmatter field is empty: %s" % key,
            ))

    identity = None
    if fields.get("id"):
        identity = check_id(fields["id"], path, findings)
    if fields.get("kind") and not KIND_RE.match(fields["kind"]):
        findings.append(Finding(
            path, ERROR,
            "kind must be lowercase letters with single hyphens between "
            "words, got %r" % fields["kind"],
        ))

    for key in order:
        if key not in REQUIRED_FIELDS:
            findings.append(Finding(
                path, WARNING,
                "field not defined by the artefact format: %s (lawful if the "
                "note's kind defines it)" % key,
            ))
    present = [key for key in order if key in REQUIRED_FIELDS]
    if len(present) == len(REQUIRED_FIELDS) and order[:4] != list(REQUIRED_FIELDS):
        findings.append(Finding(
            path, WARNING,
            "field order differs from the recommended id, name, kind, "
            "status, optional fields after",
        ))

    check_body(body_lines, fields.get("name", ""), path, findings)
    return findings, identity


def collect_notes(root):
    """The note files under a tree: .md files whose frontmatter has id or kind."""
    notes = []
    for path in sorted(Path(root).rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fields, _, _, _ = parse(text)
        if fields and ("id" in fields or "kind" in fields):
            notes.append(path)
    return notes


def check_collisions(identities, findings):
    """Error on any opaque appearing twice within one namespace."""
    seen = {}
    for path, (namespace, opaque) in identities:
        seen.setdefault((namespace, opaque.lower()), []).append(path)
    for (namespace, opaque), paths in sorted(seen.items(), key=lambda kv: str(kv[0])):
        if len(paths) > 1:
            findings.append(Finding(
                paths[-1], ERROR,
                "opaque collision: %s:%s is minted once and appears in %s"
                % (namespace, opaque, ", ".join(str(p) for p in paths)),
            ))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description=(
            "Validate Note files: the envelope, the required frontmatter "
            "(id, name, kind, status), the id grammar, and the "
            "blank-line-and-lead rule. A directory is swept recursively for "
            "note files (markdown with an id or kind field) and for opaque "
            "collisions within a namespace."
        ),
        epilog=(
            "findings go to stdout as '<path>: <level>: <message>'; the\n"
            "summary goes to stderr. Warnings never fail the run.\n"
            "\n"
            "examples:\n"
            "  validate.py corpus/req-example.md\n"
            "  validate.py path/to/corpus\n"
            "\n"
            "exit codes: 0 no violations; 1 violations; 2 bad arguments.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path", nargs="+", help="a note file, or a corpus tree to sweep",
    )
    args = parser.parse_args(argv)

    findings = []
    identities = []
    checked = 0
    for raw in args.path:
        path = Path(raw)
        if path.is_dir():
            for note in collect_notes(path):
                file_findings, identity = validate_file(note)
                findings.extend(file_findings)
                if identity:
                    identities.append((note, identity))
                checked += 1
        elif path.is_file():
            file_findings, identity = validate_file(path)
            findings.extend(file_findings)
            if identity:
                identities.append((path, identity))
            checked += 1
        else:
            parser.error("no such file or directory: %s" % raw)
    check_collisions(identities, findings)

    for finding in findings:
        print(finding)
    errors = sum(1 for f in findings if f.level == ERROR)
    warnings = sum(1 for f in findings if f.level == WARNING)
    print(
        "checked %d file(s): %d error(s), %d warning(s)"
        % (checked, errors, warnings),
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
