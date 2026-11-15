# bundle/skills/egm-drift-report

## Overview
Skill for generating drift reports comparing documentation to code.

## Interface
- `SKILL.md` — drift report workflow.

## Invariants
- `SKILL.md` frontmatter `name: egm-drift-report`.

## Side Effects
- Writes drift report artifacts to the working directory.

## Verification
- Run: `npm run validate`
