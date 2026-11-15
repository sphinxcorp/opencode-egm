# bundle

## Overview
Bundle shipped with the plugin: agents, skills, and shared resources. Source of truth for plugin content.

## Subdirectories & Boundaries
- [agents](./agents/README.md) - Reviewer persona definitions.
- [resources](./resources/README.md) - Shared runtime resources and standards.
- [skills](./skills/README.md) - EGM skill definitions.

## Global Invariants
- Every Markdown persona under `agents/` becomes a reviewer subagent.
- Every `skills/<id>/` directory with `SKILL.md` becomes a slash command and skill.
- `resources/` contains authoritative instructions and rubrics.

## Global Side Effects
- Loaded by `index.ts` at plugin setup from the `bundle/` directory adjacent to the entry point.

## System Verification
- Run: `npm run validate`
