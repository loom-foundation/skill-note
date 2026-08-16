#!/usr/bin/env python3
"""Mint a lawful Note opaque, or a full id, for a target corpus.

Draws from a secure random source and confirms uniqueness by scanning
every given corpus tree, as the method's minting procedure requires.
Python 3.9, standard library only.
"""

import argparse
import re
import secrets
import sys
from pathlib import Path

# Crockford Base32, lowercase: digits and letters minus i, l, o, u.
ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
DEFAULT_LENGTH = 7
MAX_ATTEMPTS = 100


def draw_opaque(length):
    """Draw one candidate opaque from the alphabet, securely."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def opaque_in_tree(opaque, roots):
    """True if the opaque appears, case-insensitively, in any file under roots."""
    needle = opaque.lower()
    for root in roots:
        for path in sorted(Path(root).rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if needle in text.lower():
                return True
    return False


def read_namespace(corpus):
    """Read `namespace:` from a corpus root's manifest.md, or None."""
    manifest = Path(corpus) / "manifest.md"
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^namespace:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def check_namespace(namespace):
    """Return an error message for an unlawful namespace, or None."""
    if not namespace:
        return "namespace is empty"
    if namespace != namespace.lower():
        return "namespace must be lowercase: %r" % namespace
    if ":" in namespace or any(c.isspace() for c in namespace):
        return "namespace must not contain colons or whitespace: %r" % namespace
    return None


def check_segment(segment):
    """Return an error message for an unlawful kind-segment, or None."""
    if ":" in segment or any(c.isspace() for c in segment):
        # A guard for the three-segment id grammar, not segment law.
        return "segment must not contain colons or whitespace: %r" % segment
    if not (2 <= len(segment) <= 5 and segment == segment.lower()):
        return (
            "segment must be lowercase, two to five characters: %r" % segment
        )
    return None


def mint(roots, length=DEFAULT_LENGTH, attempts=MAX_ATTEMPTS):
    """Draw until an opaque appears nowhere under roots; None if exhausted."""
    for _ in range(attempts):
        candidate = draw_opaque(length)
        if not opaque_in_tree(candidate, roots):
            return candidate
    return None


def assemble(namespace, segment, opaque):
    """Assemble the full id from its three segments."""
    return "%s:%s:%s" % (namespace, segment, opaque)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mint.py",
        description=(
            "Mint a lawful Note opaque for a target corpus, or a full id "
            "when --segment is given. The opaque is drawn from lowercase "
            "Crockford Base32 (no i, l, o, u) with a secure random source, "
            "and is confirmed absent from every given tree before it is "
            "printed."
        ),
        epilog=(
            "examples:\n"
            "  mint.py path/to/corpus\n"
            "  mint.py --segment req path/to/corpus other/repo\n"
            "  mint.py --namespace garden --length 8 path/to/corpus\n"
            "\n"
            "exit codes: 0 minted; 1 attempts exhausted; 2 bad arguments.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "corpus",
        nargs="+",
        help=(
            "corpus tree(s) to scan for uniqueness; pass every repository "
            "holding the namespace"
        ),
    )
    parser.add_argument(
        "--namespace",
        help=(
            "the id's namespace; read from the first corpus's manifest.md "
            "when omitted (needed only with --segment)"
        ),
    )
    parser.add_argument(
        "--segment",
        help="the kind-segment; when given, the full id is printed",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=DEFAULT_LENGTH,
        help="opaque length (default %(default)s, the method default)",
    )
    args = parser.parse_args(argv)

    if args.length < 1:
        parser.error("--length must be a positive integer")
    roots = []
    for corpus in args.corpus:
        path = Path(corpus)
        if not path.is_dir():
            parser.error("not a directory: %s" % corpus)
        roots.append(path)

    namespace = args.namespace
    if namespace is None:
        namespace = read_namespace(roots[0])
    if args.segment is not None:
        if namespace is None:
            parser.error(
                "no namespace: none given and none found in %s/manifest.md"
                % roots[0]
            )
        problem = check_namespace(namespace) or check_segment(args.segment)
        if problem:
            parser.error(problem)
    elif namespace is not None:
        problem = check_namespace(namespace)
        if problem:
            parser.error(problem)

    opaque = mint(roots, args.length)
    if opaque is None:
        print(
            "error: no free opaque in %d attempts; the space may be crowded, "
            "try --length %d" % (MAX_ATTEMPTS, args.length + 1),
            file=sys.stderr,
        )
        return 1

    if args.segment is not None:
        print(assemble(namespace, args.segment, opaque))
    else:
        print(opaque)
    return 0


if __name__ == "__main__":
    sys.exit(main())
