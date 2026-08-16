---
name: note
description: >
  Work a Note intent corpus: mint immutable artefact ids, validate note files and
  whole corpus trees, and author well-formed artefacts (needs, requirements,
  decisions and kin). Use this skill whenever a repository carries a Note corpus,
  recognisable by a manifest.md declaring a namespace and by markdown files whose
  frontmatter opens with an id like garden:req:t9ath61, and whenever a task
  mentions minting an id, validating notes, artefact frontmatter, kind-segments,
  opaques, or "## Relations" citations, even if the user never says Note by name.
---

# Note

A note records one piece of intent as one markdown file: YAML frontmatter carrying `id`, `name`, `kind`, `status`, then a body opening with an unheaded lead.
Its `id` is `<namespace>:<kind-segment>:<opaque>`, minted once and never changed; identity is the namespace and the opaque, and the segment is display, rendered from `kind`.
The namespace is declared once in the corpus's `manifest.md`; the opaque is lowercase Crockford Base32 (digits and letters minus `i`, `l`, `o`, `u`), unique within its namespace across every kind.

## Mint an id

Never invent an opaque; draw one and prove it free:

```sh
python3 scripts/mint.py --segment req path/to/corpus [other/repo ...]
```

Pass every repository holding the namespace; it is read from the `namespace:` field in the YAML frontmatter of the first one's `manifest.md` (`namespace: garden`).
`--segment` is the kind's abbreviation (`req` for a requirement); omit it to print a bare opaque.
Run with `--help` for the full contract.

## Validate a note

Run after authoring and after any bulk edit:

```sh
python3 scripts/validate.py path/to/note.md    # one file
python3 scripts/validate.py path/to/corpus     # whole tree, plus a collision sweep
```

Exit 0 means clean; findings go to stdout, and warnings never fail a run.
Run with `--help` for the full contract.

## Author a note

Copy the nearest example from `resources/templates/` (a need, a requirement, a decision), follow the placeholder conventions in that directory's `README.md`, mint a fresh id, and validate.
Keep only the sections that carry substance.

## Load on demand

Read the reference that matches the task in hand; none is loaded by default.

- `resources/docs/identifiers.md`: the id grammar, identity versus display, immutability, minting by hand, unknown kinds.
- `resources/docs/note-file.md`: the envelope, required frontmatter and quoting, the body and its lead, `## Relations` lines.
- `resources/docs/schema.md`: the structural rules behind both, and the boundary of what is fixed.

## Boundaries

Status values and their transitions are undefined today: accept any non-empty `status` token and state no rule about them.
Enforce nothing these files do not state; the method fixes more only as its corpus grows.
