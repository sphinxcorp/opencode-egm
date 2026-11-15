# bundle/skills/egm-brainstorm

## Overview
Skill for structured brainstorming before drafting, dispatching seven brainstorm reviewers.

## Interface
- `SKILL.md` — brainstorm workflow and reviewer dispatch instructions.

## Invariants
- `SKILL.md` frontmatter `name: egm-brainstorm`.
- Requires completion of all seven brainstorm reviewers before synthesis.

## Side Effects
- Produces `concepts_brief.md` in the working directory.

## Verification
- Run: `npm run validate`
