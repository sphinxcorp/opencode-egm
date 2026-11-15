# bundle/skills/egm-bootstrap

## Overview
Skill that bootstraps EGM-compliant README contract files across a directory tree (peanuts and hay).

## Interface
- `SKILL.md` — full workflow, templates reference, worker return contract.
- `references/templates.md` — README templates.
- `references/worker-return.schema.json` — worker payload schema.

## Invariants
- `SKILL.md` frontmatter `name: egm-bootstrap`.
- References must resolve under `references/`.

## Side Effects
- Writes/corrects `README.md` (or configured target filename) files in target tree; no source code changes.

## Verification
- Run: `npm run validate`
