# bundle/skills/egm-bootstrap/references

## Overview
Templates and return-schema references consumed by the egm-bootstrap skill.

## Interface
- `templates.md` — Component Package, Repository Root, and Intermediate Blueprint README templates.
- `worker-return.schema.json` — JSON schema for worker subtree_index payloads.

## Invariants
- Paths are resolved relative to the skill directory (`references/...`).
- `SKILL.md` references these files by relative path; validation requires they exist.

## Side Effects
- None; read-only reference assets.

## Verification
- Run: `npm run validate`
