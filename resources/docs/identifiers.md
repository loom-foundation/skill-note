# Identifiers

Every note carries an immutable `id` of three colon-separated segments: `<namespace>:<kind-segment>:<opaque>` (example: `garden:idea:7fjq3ka`).
Identity is the namespace and the opaque; the kind-segment between them is display, rendered from the note's `kind` field, and never part of identity.

## The grammar

| Segment | Rule |
|---|---|
| namespace | Declared once, as the `namespace:` field in the corpus's `manifest.md` frontmatter (`namespace: garden`); short, lowercase, distinctive, partitioning the identity space so distinct bodies of work take distinct namespaces. |
| kind-segment | An abbreviation rendered from the authoritative `kind` field; every kind carries exactly one segment, shared with no other kind. |
| opaque | Crockford Base32, lowercase: `0123456789abcdefghjkmnpqrstvwxyz` (`i`, `l`, `o`, `u` excluded); compared case-insensitively; unique within its namespace across every kind. |

The opaque's default length is seven characters.
Each corpus configures its own length, governing new ids only; mixed lengths are lawful within one namespace, and opaques of different lengths never collide.

## Identity versus display

- Two ids denote the same note exactly when their namespaces and their opaques are equal, the opaques compared case-insensitively; the segment plays no part.
- To find every mention of a note, match the namespace and the opaque, never the full spelling, which a wrong segment could hide.
- A segment disagreeing with `kind` is a display defect: repair it from the note's own `kind` wherever the spelling can be edited.
  It never changes which note the id denotes.
- A segment fixed where you cannot edit it (a commit message, a published copy) records the target's kind as of the citation.
  It is history, not a defect; never rewrite it.

## Immutability

An id is minted once and never changes: not on a move, a rename, or a revision.
Reopening a settled question is a new note with a new id.

## Minting

1. Draw the opaque's characters from the alphabet above, using a secure random source.
2. Confirm the string appears nowhere the namespace is kept: `grep -ri <opaque>` in every repository holding it; silence means it is free.
3. Assemble `<namespace>:<segment>:<opaque>`, the segment rendered from the note's `kind`.

`scripts/mint.py` performs all three steps; run `python3 scripts/mint.py --help`.
It reads the namespace from the target corpus's `manifest.md`, or takes `--namespace` where no manifest is in reach.

## Unknown kinds

A well-formed kind token nothing yet defines still makes a note; the unknown token is a warning, never a bar on the file.
For such a kind, write the full token in `kind` and choose your own abbreviation for the segment: provisional until the kind is defined, canonical after.
