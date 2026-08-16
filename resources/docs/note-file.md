# The note file

A note is a single UTF-8 text file: YAML frontmatter between two `---` lines, exactly one blank line, then a markdown body.
One note per file.
The file's name is a navigation convenience, never the identity, so a name alone never decides whether a file is a valid note.

## Frontmatter

The frontmatter is YAML 1.2 under the core schema, so every conforming reader resolves a value's type from its spelling the same way.

Four fields are required:

| Field | Value |
|---|---|
| `id` | `<namespace>:<kind-segment>:<opaque>`, immutable; see [identifiers.md](./identifiers.md). |
| `name` | A concise label, never a summary. |
| `kind` | The kind token: lowercase letters with single hyphens between words, authoritative for the id's kind-segment. |
| `status` | A required token recording where the note stands. |

Write the fields in the recommended order `id`, `name`, `kind`, `status`, optional fields after them, so same-shaped notes diff precisely.
The order is recommended, never required: any other order is never rejected while the required fields stand.

Two quoting rules cover everything you will meet:

- Quote a value containing a colon followed by a space (`name: "Warp: the frame"`); unquoted, it parses as a nested mapping.
- Quote a value whose spelling reads as a number, boolean, or null (`name: "42"`); unquoted, it stops being text.

A frontmatter field neither the format nor the note's kind defines is a warning, reported by name, preserved untouched by any tool that rewrites the note, and never an error.

## Body

- Exactly one blank line separates the closing `---` from the lead.
- The lead is unheaded: one statement of the note's substance, with no level-1 heading anywhere in the body, and the name never repeated as a heading.
- Section headings are level 2. Each kind fixes their recommended order; a different order is never rejected while the sections the kind requires stand.

## Relations

Relations live in a `## Relations` body section, one list entry per relation:

```
- <verb>: [<name>](<relative path>){id=<id>}
```

The `{id=...}` attribute is the citation.
Sweeps match its namespace and opaque, never the path or the label, so a moved file or a stale label never hides a relation.

## Well-formed

A note is well-formed with a well-formed envelope, the four required fields, whatever its kind requires of it, and a lead.
`scripts/validate.py` checks one file or a whole corpus tree; run `python3 scripts/validate.py --help`.
