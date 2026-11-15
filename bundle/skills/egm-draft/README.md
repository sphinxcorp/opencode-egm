# bundle/skills/egm-draft

## Overview
Skill for drafting design documents from a concepts brief.

## Interface
- `SKILL.md` — drafting workflow.
- `references/design_doc.md` — design document standard.

## Invariants
- `SKILL.md` frontmatter `name: egm-draft`.
- References must resolve under `references/`.

## Side Effects
- Writes design document artifacts to the working directory.

## Verification
- Run: `npm run validate`
