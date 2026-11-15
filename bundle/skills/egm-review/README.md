# bundle/skills/egm-review

## Overview
Skill for dispatching reviewer agents against a target document.

## Interface
- `SKILL.md` — review workflow and reviewer dispatch.

## Invariants
- `SKILL.md` frontmatter `name: egm-review`.

## Side Effects
- Writes review report artifacts to the working directory.

## Verification
- Run: `npm run validate`
