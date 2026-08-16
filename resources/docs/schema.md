# The structural schema

Note's structure is fixed in one normalised data model, the single source of truth for structure; the markdown medium of plain files, frontmatter, and the `## Relations` section implements it as faithfully as it allows.
The model fixes structure alone; meaning stays with the notes' prose.
These are its rules as you apply them to files.

## The note

- One markdown file is one record; its fields surface as the frontmatter `id`, `name`, `kind`, and `status`.
- The key is the namespace and the opaque. Within one namespace an opaque appears once, across every kind: two files sharing a namespace and an opaque are a collision, an error.
- The namespace and the opaque are lowercase.
- `status` is required; no value set is fixed today, so any non-empty token stands.

## The kind register

- Every kind token carries exactly one id segment, and no two kinds share a segment.
- A kind token is lowercase letters with single hyphens between words.
- A segment is lowercase, two to five characters.
- A well-formed token no register defines still makes a note; the unknown token is a warning, never a bar on the file.

## Derived, never stored

- The id's kind-segment is always rendered from `kind`, never kept as a fact of its own; that is the schema's statement that the segment is not identity.
- An id is minted once and never changes; a changed id reads as a new note.

## Not yet fixed

The model fixes nothing beyond these rules today.
In particular, `status` values and their transitions are undefined; state no rule about them.
