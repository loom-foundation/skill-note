# Note Skill

The note skill: the Note method distilled for AI agents, with scripts and templates.
`SKILL.md` is the front door; everything deeper is loaded on demand.

- `SKILL.md`: the essential instructions, with pointers to everything below.
- `resources/docs/`: the distilled references, covering identity, the note file, and the structural schema.
- `resources/templates/`: worked example artefacts to copy from.
- `scripts/`: `mint.py` and `validate.py`, Python 3.9 standard-library command-line tools; each documents itself under `--help`.
- `tests/`: the unittest suites.
- `note/`: the skill's own note corpus, the intent behind it.

`./check` at the root runs every test; CI runs exactly that.
