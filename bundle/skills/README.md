# bundle/skills

## Overview
Collection of EGM skill definitions, each a directory with `SKILL.md` and optional `references/`.

## Subdirectories & Boundaries
- [egm-bootstrap](./egm-bootstrap/README.md) - Bootstraps directory README contracts.
- [egm-bootstrap/references](./egm-bootstrap/references/README.md) - Templates and worker schema.
- [egm-brainstorm](./egm-brainstorm/README.md) - Brainstorming workflow.
- [egm-draft](./egm-draft/README.md) - Drafting workflow.
- [egm-draft/references](./egm-draft/references/README.md) - Design document standard.
- [egm-drift-report](./egm-drift-report/README.md) - Drift reporting workflow.
- [egm-resolve](./egm-resolve/README.md) - Finding resolution workflow.
- [egm-review](./egm-review/README.md) - Review dispatch workflow.
- [egm-review-loop](./egm-review-loop/README.md) - Iterative review loop workflow.

## Global Invariants
- Each skill directory must contain `SKILL.md` with frontmatter `name`.
- Referenced files under `references/` must exist (validated by `npm run validate`).

## Global Side Effects
- Skills are loaded by `index.ts` (`loadSkills`) and registered as slash commands and skills.

## System Verification
- Run: `npm test`
