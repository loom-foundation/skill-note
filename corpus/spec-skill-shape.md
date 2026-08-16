---
id: skillnote:spec:fbr7v83
name: The skill's shape
kind: specification
status: current
---

This specification fixes the repository's shape: what sits where, and what each part carries.

- `SKILL.md`, at the root: the front door, frontmatter name and description tuned for triggering, then the essential instructions with pointers to everything below.
- `resources/docs/`: the distilled explanation of how Note works, structured markdown covering identity, the note file envelope, and the structural schema.
- `resources/templates/`: example artefacts, well-formed and best practice, that agents copy from.
- `scripts/`: the codified common operations, `mint.py` and `validate.py`, each a command-line tool that documents itself under `--help`.
- `tests/`: the scripts' unittest suites, run by one `./check` at the repository root.
- `corpus/`: this corpus, the intent behind the skill.

## Relations

- satisfies: [SKILL.md fits one read and defers](./req-progressive-disclosure.md){id=skillnote:req:vf0ave4}
- satisfies: [Checked scripts on the standard library](./req-checked-tooling.md){id=skillnote:req:8pz0cz8}
